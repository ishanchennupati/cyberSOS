"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { ErrorState } from "@/components/error-state";
import { FlowNav } from "@/components/flow-nav";
import { LoadingState } from "@/components/loading-state";
import { ProgressSteps } from "@/components/progress-steps";
import { StepAmount } from "@/components/steps/step-amount";
import { StepCrimeCategory } from "@/components/steps/step-crime-category";
import { StepIncidentType } from "@/components/steps/step-incident-type";
import { GuidedCrimeQuestions, guidedQuestionLabels, type GuidedCrimeDetails } from "@/components/steps/guided-crime-questions";
import { StepSituation, type SituationId } from "@/components/steps/step-situation";
import { StepTransactionId } from "@/components/steps/step-transaction-id";
import { StepWhen } from "@/components/steps/step-when";
import { createIncident, triageIncident, getIncident, uploadEvidence, ApiError } from "@/lib/api";
import { parseAmountInput } from "@/lib/format";
import {
  fromDateTimeLocalValue,
  occurredAtFromPreset,
  toDateTimeLocalValue,
  type TimePreset,
} from "@/lib/time-presets";
import type {
  IncidentType,
  OtherCrimeSubCategory,
  PaymentMethod,
  TopLevelCrimeCategory,
} from "@/types/incident";

const FINANCIAL_STEPS = [
  { label: "Category" },
  { label: "What happened" },
  { label: "Type" },
  { label: "When" },
  { label: "Amount" },
  { label: "UTR" },
];

type FlowState = {
  category: TopLevelCrimeCategory | null;
  situation: SituationId | null;
  situationDescription?: string;
  incidentId: string | null;
  incidentType: IncidentType | null;
  otherSubCategory: OtherCrimeSubCategory | null;
  otherDetails: GuidedCrimeDetails;
  timePreset: TimePreset | null;
  exactValue: string;
  amount: string;
  paymentMethod: PaymentMethod | null;
  transactionId: string;
  transactionStatus: "unknown" | "pending" | "completed";
  ongoingRisk: boolean;
  evidenceFiles: File[];
};

const INITIAL_STATE: FlowState = {
  category: null,
  situation: null,
  situationDescription: "",
  incidentId: null,
  incidentType: null,
  otherSubCategory: null,
  otherDetails: {},
  timePreset: null,
  exactValue: "",
  amount: "",
  paymentMethod: null,
  transactionId: "",
  transactionStatus: "unknown",
  ongoingRisk: false,
  evidenceFiles: [],
};

function IncidentStartFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("id");

  // If we're editing an existing incident, skip the category picker (step 0)
  // and land directly on the financial sub-flow, whose first step is 1.
  const [step, setStep] = useState(editId ? 1 : 0);
  const [guidedIndex, setGuidedIndex] = useState(0);
  const [flow, setFlow] = useState<FlowState>(INITIAL_STATE);
  const [errorMessage, setErrorMessage] = useState("");
  const [busy, setBusy] = useState(false);

  // Load state from sessionStorage or API
  useEffect(() => {
    if (!editId) return;
    const id = editId;

    async function load() {
      setBusy(true);
      try {
        const cached = sessionStorage.getItem(`cybersos_flow_${id}`);
        if (cached) {
          const parsed = JSON.parse(cached) as FlowState;
          setFlow(parsed);
          return;
        }

        const incident = await getIncident(id);

        // Infer a sensible default situation
        let inferredSituation: SituationId = "money_taken";
        if (incident.incident_type !== "financial_fraud") {
          inferredSituation = "other_cybercrime";
        }

        setFlow((prev) => ({
          ...prev,
          category: "financial_fraud",
          situation: inferredSituation,
          situationDescription: "",
          incidentId: incident.id,
          incidentType: incident.incident_type,
          timePreset: "exact",
          exactValue: incident.occurred_at ? toDateTimeLocalValue(new Date(incident.occurred_at)) : "",
          amount: incident.amount !== null ? String(incident.amount) : "",
          paymentMethod: incident.payment_method,
          transactionId: incident.transaction_id || "",
        }));
      } catch (err) {
        setErrorMessage("Failed to load your incident details.");
      } finally {
        setBusy(false);
      }
    }

    void load();
  }, [editId]);

  // Save state to sessionStorage when it changes
  useEffect(() => {
    if (flow.incidentId) {
      sessionStorage.setItem(`cybersos_flow_${flow.incidentId}`, JSON.stringify(flow));
    }
  }, [flow]);

  const isFinancial = flow.category === "financial_fraud";
  const isOther = flow.category === "other_cyber_crime";
  const guidedCategory = flow.category === "women_children" ? "women_children" : "other_cyber_crime";
  const steps = isOther || flow.category === "women_children"
    ? [{ label: "Category" }, ...guidedQuestionLabels(guidedCategory, flow.otherSubCategory, flow.otherDetails).map((label) => ({ label }))]
    : FINANCIAL_STEPS;

  function update<K extends keyof FlowState>(key: K, value: FlowState[K]) {
    setFlow((prev) => ({ ...prev, [key]: value }));
    setErrorMessage("");
  }

  function resolvedOccurredAt(): Date | null {
    if (flow.timePreset === "exact") return fromDateTimeLocalValue(flow.exactValue);
    if (flow.timePreset) return occurredAtFromPreset(flow.timePreset);
    const guidedDate = String(flow.otherDetails.incident_date_time ?? "");
    const preset = String(flow.otherDetails.incident_time ?? "");
    const age: Record<string, number> = { "Just now": 0, "Within the last 24 hours": 1, "Within the last week": 3, "Within the last month": 14, "More than a month ago": 60 };
    if (preset in age) return new Date(Date.now() - age[preset] * 24 * 60 * 60 * 1000);
    if (guidedDate) {
      const parsed = new Date(guidedDate);
      if (!Number.isNaN(parsed.getTime())) return parsed;
    }
    return null;
  }

  function validateStep(current: number): string | null {
    if (current === 0 && !flow.category) return "Please choose the type of cyber crime.";
    if (flow.category === "women_children") return null;
    if (isFinancial && current === 1 && !flow.situation) return "Please choose the option that best matches what happened.";
    if (isFinancial && current === 2) {
      if (!flow.incidentType) return "Please select an incident type to continue.";
      if (flow.incidentType !== "financial_fraud") return "This type isn't available yet. Please choose UPI / financial fraud.";
    }
    if (isFinancial && current === 3) {
      if (!flow.timePreset) return "Please tell us when this happened - it decides how urgently you need to act.";
      const occurred = resolvedOccurredAt();
      if (!occurred) return "Please enter the date and time of the transaction.";
      if (occurred.getTime() > Date.now() + 60 * 1000) return "That time is in the future. Please check the date and time.";
    }
    if (isFinancial && current === 4) {
      const amount = parseAmountInput(flow.amount);
      if (amount === null || amount <= 0) return "Please enter the amount that left your account.";
      if (!flow.paymentMethod || flow.paymentMethod === "unknown") return "Please select how the payment was made.";
    }
    return null;
  }

  async function finishGuidedCrime() {
    const occurred = resolvedOccurredAt();
    const incidentType = flow.category === "women_children" ? "women_children" : "other_cyber_crime";
    if (!String(flow.otherDetails.incident_subtype ?? "") || !occurred) {
      setErrorMessage("Some details are missing. Please go back and check each step.");
      return;
    }
    setBusy(true);
    try {
      const incident = await createIncident({
        incident_type: incidentType,
        incident_subtype: String(flow.otherDetails.incident_subtype ?? ""),
        affected_person_type: String(flow.otherDetails.affected_person_type ?? "") || null,
        platform: String(flow.otherDetails.platform ?? "") || null,
        account_type: String(flow.otherDetails.account_type ?? "") || null,
        immediate_danger: flow.otherDetails.immediate_danger === "Yes",
        threat_or_blackmail: flow.otherDetails.threat_or_blackmail === "Yes",
        content_still_online: flow.otherDetails.content_still_online === "Yes",
        account_access: String(flow.otherDetails.account_access ?? "") || null,
        attacker_active: flow.otherDetails.attacker_active === "Yes",
        sensitive_information_exposed: flow.otherDetails.sensitive_information_exposed === "Yes",
        evidence_types: Array.isArray(flow.otherDetails.evidence_types) ? flow.otherDetails.evidence_types : [],
        payment_method: "unknown",
        details: flow.otherDetails,
      });
      await triageIncident(incident.id, {
        incident_type: incidentType,
        incident_subtype: String(flow.otherDetails.incident_subtype ?? ""),
        affected_person_type: String(flow.otherDetails.affected_person_type ?? "") || null,
        platform: String(flow.otherDetails.platform ?? "") || null,
        account_type: String(flow.otherDetails.account_type ?? "") || null,
        immediate_danger: flow.otherDetails.immediate_danger === "Yes",
        threat_or_blackmail: flow.otherDetails.threat_or_blackmail === "Yes",
        content_still_online: flow.otherDetails.content_still_online === "Yes",
        account_access: String(flow.otherDetails.account_access ?? "") || null,
        attacker_active: flow.otherDetails.attacker_active === "Yes",
        sensitive_information_exposed: flow.otherDetails.sensitive_information_exposed === "Yes",
        evidence_types: Array.isArray(flow.otherDetails.evidence_types) ? flow.otherDetails.evidence_types : [],
        occurred_at: occurred.toISOString(),
        payment_method: "unknown",
        details: flow.otherDetails,
      });
      await Promise.all(flow.evidenceFiles.map((file) => uploadEvidence(incident.id, file)));
      router.push(`/incident/${incident.id}/result`);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setBusy(false);
    }
  }

  async function handleNext() {
    const validationError = validateStep(step);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }
    setErrorMessage("");

    if (step === 0) {
      if (flow.category === "financial_fraud") {
        setFlow((prev) => ({ ...prev, incidentType: "financial_fraud" }));
        setStep(1);
      } else if (flow.category === "other_cyber_crime") {
        setGuidedIndex(0);
        setStep(1);
      } else if (flow.category === "women_children") {
        setGuidedIndex(0);
        setStep(1);
      }
      return;
    }

    if (flow.category === "women_children") {
      await finishGuidedCrime();
      return;
    }

    if (isOther) {
      await finishGuidedCrime();
      return;
    }

    if (step === 1) {
      if (flow.incidentId) {
        setStep(2);
        return;
      }
      setBusy(true);
      try {
        const incident = await createIncident({
          incident_type: "financial_fraud",
          payment_method: "unknown",
        });
        setFlow((prev) => ({ ...prev, incidentId: incident.id }));
        setStep(2);
      } catch (err) {
        setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      } finally {
        setBusy(false);
      }
      return;
    }

    if (step < 5) {
      setStep(step + 1);
      return;
    }

    const occurred = resolvedOccurredAt();
    const amount = parseAmountInput(flow.amount);
    if (!flow.incidentId || !flow.incidentType || !occurred || amount === null || !flow.paymentMethod) {
      setErrorMessage("Some details are missing. Please go back and check each step.");
      return;
    }

    setBusy(true);
    try {
      await triageIncident(flow.incidentId, {
        incident_type: flow.incidentType,
        occurred_at: occurred.toISOString(),
        amount,
        payment_method: flow.paymentMethod,
        transaction_id: flow.transactionId.trim() ? flow.transactionId.trim() : null,
        transaction_status: flow.transactionStatus,
        unauthorized_activity_continuing: flow.ongoingRisk,
        potential_additional_loss: flow.ongoingRisk,
      });
      router.push(`/incident/${flow.incidentId}/result`);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setBusy(false);
    }
  }

  function handleBack() {
    setErrorMessage("");
    if (step === 0) return;
    setStep(step - 1);
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2 text-sm text-ink-muted hover:text-ink">
            <ArrowLeft size={16} aria-hidden="true" />
            Back
          </Link>
          <span className="font-display text-lg italic text-ink">CyberSOS</span>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <ProgressSteps
          steps={steps}
          currentStep={isOther || flow.category === "women_children" ? guidedIndex + 2 : step + 1}
        />

        <div className="mt-10">
          {step === 0 && (
            <StepCrimeCategory
              value={flow.category}
              onChange={(value) => {
                update("category", value);
                setGuidedIndex(0);
              }}
            />
          )}
          {(isOther || flow.category === "women_children") && step === 1 && (
            <GuidedCrimeQuestions
              category={flow.category === "women_children" ? "women_children" : "other_cyber_crime"}
              subCategory={flow.otherSubCategory}
              details={flow.otherDetails}
              evidenceFiles={flow.evidenceFiles}
              onSubCategoryChange={(value) => update("otherSubCategory", value)}
              onDetailsChange={(value) => update("otherDetails", value)}
              onEvidenceFilesChange={(value) => update("evidenceFiles", value)}
              onProgress={setGuidedIndex}
              onComplete={() => void finishGuidedCrime()}
            />
          )}
          {isFinancial && step === 1 && (
            <StepSituation
              value={flow.situation}
              onChange={(value) => update("situation", value)}
              description={flow.situationDescription || ""}
              onDescriptionChange={(value) => update("situationDescription", value)}
            />
          )}
          {isFinancial && step === 2 && (
            <StepIncidentType value={flow.incidentType} onChange={(value) => update("incidentType", value)} />
          )}
          {isFinancial && step === 3 && (
            <StepWhen
              preset={flow.timePreset}
              exactValue={flow.exactValue}
              onPreset={(preset) => {
                const nextExact =
                  preset === "exact"
                    ? flow.exactValue || toDateTimeLocalValue(new Date())
                    : toDateTimeLocalValue(occurredAtFromPreset(preset));
                setFlow((prev) => ({ ...prev, timePreset: preset, exactValue: nextExact }));
                setErrorMessage("");
              }}
              onExactChange={(value) => {
                setFlow((prev) => ({ ...prev, timePreset: "exact", exactValue: value }));
                setErrorMessage("");
              }}
            />
          )}
          {isFinancial && step === 4 && (
            <StepAmount
              amount={flow.amount}
              paymentMethod={flow.paymentMethod}
              onAmountChange={(value) => update("amount", value)}
              onPaymentMethodChange={(value) => update("paymentMethod", value)}
            />
          )}
          {isFinancial && step === 5 && (
            <StepTransactionId value={flow.transactionId} onChange={(value) => update("transactionId", value)} status={flow.transactionStatus} onStatusChange={(value) => update("transactionStatus", value)} ongoing={flow.ongoingRisk} onOngoingChange={(value) => update("ongoingRisk", value)} />
          )}

          {busy && (
            <div className="mt-6">
              <LoadingState message={step === 5 || isOther ? "Working out what you should do first..." : "Starting your incident..."} />
            </div>
          )}

          {errorMessage && !busy && (
            <div className="mt-6">
              <ErrorState message={errorMessage} onRetry={handleNext} />
            </div>
          )}

          {flow.category === "financial_fraud" || step === 0 ? (
            <FlowNav
              onBack={step > 0 ? handleBack : undefined}
              onNext={handleNext}
              nextLabel={isFinancial && step === 5 ? "See what to do now" : "Continue"}
              busy={busy}
            />
          ) : null}
        </div>
      </div>
    </main>
  );
}

export default function IncidentStartPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-paper flex items-center justify-center">
        <LoadingState message="Loading..." />
      </main>
    }>
      <IncidentStartFlow />
    </Suspense>
  );
}