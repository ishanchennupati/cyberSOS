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
import { StepIncidentType } from "@/components/steps/step-incident-type";
import { StepOtherCrimeDetails, type OtherCrimeDetails } from "@/components/steps/step-other-crime-details";
import { StepSituation, type SituationId } from "@/components/steps/step-situation";
import { StepTransactionId } from "@/components/steps/step-transaction-id";
import { StepWhen } from "@/components/steps/step-when";
import { GuidedCrimeQuestions, type GuidedCrimeDetails } from "@/components/steps/guided-crime-questions";
import { createIncident, triageIncident, getIncident, uploadEvidence, ApiError } from "@/lib/api";
import { parseAmountInput } from "@/lib/format";
import {
  fromDateTimeLocalValue,
  occurredAtFromPreset,
  toDateTimeLocalValue,
  type TimePreset,
} from "@/lib/time-presets";
import type { IncidentType, OtherCrimeSubCategory, PaymentMethod } from "@/types/incident";

const MAX_INCIDENT_AMOUNT = 9_999_999_999.99;

const STEPS = [
  { label: "What happened" },
  { label: "Type" },
  { label: "When" },
  { label: "Amount" },
  { label: "UTR" },
];

type FlowState = {
  situation: SituationId | null;
  situationDescription?: string;
  incidentId: string | null;
  incidentType: IncidentType | null;
  timePreset: TimePreset | null;
  exactValue: string;
  amount: string;
  paymentMethod: PaymentMethod | null;
  transactionId: string;
  transactionStatus: "unknown" | "pending" | "completed";
  ongoingRisk: boolean;
  otherCrimeSubCategory: OtherCrimeSubCategory | null;
  otherCrimeDetails: OtherCrimeDetails;
  womenChildrenDetails: GuidedCrimeDetails;
  evidenceFiles: File[];
};

const INITIAL_STATE: FlowState = {
  situation: null,
  situationDescription: "",
  incidentId: null,
  incidentType: null,
  timePreset: null,
  exactValue: "",
  amount: "",
  paymentMethod: null,
  transactionId: "",
  transactionStatus: "unknown",
  ongoingRisk: false,
  otherCrimeSubCategory: null,
  otherCrimeDetails: {},
  womenChildrenDetails: {},
  evidenceFiles: [],
};

function IncidentStartFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("id");

  const [step, setStep] = useState(1);
  const [flow, setFlow] = useState<FlowState>(INITIAL_STATE);
  const [errorMessage, setErrorMessage] = useState("");
  const [busy, setBusy] = useState(false);

  // Load state from sessionStorage or API
  useEffect(() => {
    if (!editId) return;
    const incidentId = editId;

    async function load() {
      setBusy(true);
      try {
        const cached = sessionStorage.getItem(`cybersos_flow_${incidentId}`);
        if (cached) {
          const parsed = JSON.parse(cached) as FlowState;
          setFlow(parsed);
          return;
        }

        const incident = await getIncident(incidentId);
        
        // Infer a sensible default situation
        let inferredSituation: SituationId = "money_taken";
        if (incident.incident_type !== "financial_fraud") {
          inferredSituation = "other_cybercrime";
        }

        setFlow({
          situation: inferredSituation,
          situationDescription: "",
          incidentId: incident.id,
          incidentType: incident.incident_type,
          timePreset: "exact",
          exactValue: incident.occurred_at ? toDateTimeLocalValue(new Date(incident.occurred_at)) : "",
          amount: incident.amount !== null ? String(incident.amount) : "",
          paymentMethod: incident.payment_method,
          transactionId: incident.transaction_id || "",
          transactionStatus:
            incident.transaction_status === "pending" || incident.transaction_status === "completed"
              ? incident.transaction_status
              : "unknown",
          ongoingRisk: Boolean(incident.unauthorized_activity_continuing),
          otherCrimeSubCategory: incident.other_crime_sub_category,
          otherCrimeDetails: (incident.details ?? {}) as OtherCrimeDetails,
          womenChildrenDetails: incident.incident_type === "women_children"
            ? ((incident.details ?? {}) as GuidedCrimeDetails)
            : {},
          evidenceFiles: [],
        });
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

  function update<K extends keyof FlowState>(key: K, value: FlowState[K]) {
    setFlow((prev) => ({ ...prev, [key]: value }));
    setErrorMessage("");
  }

  function resolvedOccurredAt(): Date | null {
    if (flow.timePreset === "exact") {
      return fromDateTimeLocalValue(flow.exactValue);
    }
    if (flow.timePreset) {
      return occurredAtFromPreset(flow.timePreset);
    }
    return null;
  }

  function resolvedWomenOccurredAt(): Date | null {
    const label = String(flow.womenChildrenDetails.incident_time ?? "");
    const days: Record<string, number> = {
      "Just now": 0,
      "Within the last 24 hours": 1,
      "Within the last week": 3,
      "Within the last month": 14,
      "More than a month ago": 60,
    };
    return label in days ? new Date(Date.now() - days[label] * 24 * 60 * 60 * 1000) : null;
  }

  async function finishWomenChildren() {
    const details = flow.womenChildrenDetails;
    const occurred = resolvedWomenOccurredAt();
    if (!occurred || !String(details.incident_subtype ?? "")) {
      setErrorMessage("Some safety details are missing. Please go back and check each step.");
      return;
    }
    setBusy(true);
    try {
      const incident = flow.incidentId ? await getIncident(flow.incidentId) : await createIncident({ incident_type: "women_children", payment_method: "unknown" });
      if (!flow.incidentId) setFlow((prev) => ({ ...prev, incidentId: incident.id }));
      await triageIncident(incident.id, {
        incident_type: "women_children",
        incident_subtype: String(details.incident_subtype),
        occurred_at: occurred.toISOString(),
        payment_method: "unknown",
        affected_person_type: String(details.affected_person_type ?? "") || null,
        immediate_danger: details.immediate_danger === "Yes",
        threat_or_blackmail: details.threat_or_blackmail === "Yes",
        content_still_online: details.content_still_online === "Yes",
        evidence_types: Array.isArray(details.evidence_types) ? details.evidence_types : [],
        details,
      });
      await Promise.all(flow.evidenceFiles.map((file) => uploadEvidence(incident.id, file)));
      router.push(`/incident/${incident.id}/result`);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setBusy(false);
    }
  }

  function validateStep(current: number): string | null {
    if (current === 1 && !flow.situation) {
      return "Please choose the option that best matches what happened.";
    }
    if (current === 2) {
      if (!flow.incidentType) {
        return "Please select an incident type to continue.";
      }
    }
    if (current === 3) {
      if (flow.incidentType === "other_cyber_crime") {
        if (!flow.otherCrimeSubCategory) {
          return "Please select the type of other cyber crime.";
        }
        return null;
      }
      if (!flow.timePreset) {
        return "Please tell us when this happened — it decides how urgently you need to act.";
      }
      const occurred = resolvedOccurredAt();
      if (!occurred) {
        return "Please enter the date and time of the transaction.";
      }
      if (occurred.getTime() > Date.now() + 60 * 1000) {
        return "That time is in the future. Please check the date and time.";
      }
    }
    if (current === 4) {
      if (flow.incidentType === "other_cyber_crime") {
        if (!flow.timePreset) {
          return "Please tell us when this happened — it decides how urgently you need to act.";
        }
        const occurred = resolvedOccurredAt();
        if (!occurred) return "Please enter the date and time of the incident.";
        if (occurred.getTime() > Date.now() + 60 * 1000) {
          return "That time is in the future. Please check the date and time.";
        }
        return null;
      }
      const amount = parseAmountInput(flow.amount);
      if (amount === null || amount <= 0) {
        return "Please enter the amount that left your account.";
      }
      if (amount > MAX_INCIDENT_AMOUNT) {
        return "Please enter an amount of 9,999,999,999.99 or less.";
      }
      if (!flow.paymentMethod) {
        return "Please select how the payment was made.";
      }
    }
    return null;
  }

  async function handleNext() {
    const validationError = validateStep(step);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }
    setErrorMessage("");

    if (step === 1) {
      if (flow.incidentId) {
        setStep(2);
        return;
      }
      setBusy(true);
      try {
        const incident = await createIncident({
          incident_type: flow.situation === "women_children" ? "women_children" : "financial_fraud",
          payment_method: "unknown",
        });
        setFlow((prev) => ({ ...prev, incidentId: incident.id }));
        setStep(2);
      } catch (err) {
        setErrorMessage(
          err instanceof ApiError ? err.message : "Something went wrong. Please try again."
        );
      } finally {
        setBusy(false);
      }
      return;
    }

    if (step < 5) {
      if (step === 2 && flow.situation === "women_children") return;
      setStep(step + 1);
      return;
    }

    const occurred = resolvedOccurredAt();
    const amount = parseAmountInput(flow.amount);
    const isOtherCrime = flow.incidentType === "other_cyber_crime";
    if (!flow.incidentId || !flow.incidentType || !occurred || (!isOtherCrime && (amount === null || !flow.paymentMethod))) {
      setErrorMessage("Some details are missing. Please go back and check each step.");
      return;
    }

    setBusy(true);
    try {
      await triageIncident(flow.incidentId, {
        incident_type: flow.incidentType,
        occurred_at: occurred.toISOString(),
        amount: isOtherCrime ? null : amount,
        payment_method: isOtherCrime ? "unknown" : flow.paymentMethod!,
        transaction_id: flow.transactionId.trim() ? flow.transactionId.trim() : null,
        other_crime_sub_category: isOtherCrime ? flow.otherCrimeSubCategory : null,
        details: isOtherCrime
          ? { ...flow.otherCrimeDetails, situation_description: flow.situationDescription || undefined }
          : null,
        transaction_status: flow.transactionStatus,
        unauthorized_activity_continuing: flow.ongoingRisk,
        potential_additional_loss: flow.ongoingRisk,
      });
      router.push(`/incident/${flow.incidentId}/result`);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again."
      );
      setBusy(false);
    }
  }

  function handleBack() {
    setErrorMessage("");
    if (step === 1) return;
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
        <ProgressSteps steps={STEPS} currentStep={step} />

        <div className="mt-10">
          {step === 1 && (
            <StepSituation
              value={flow.situation}
              onChange={(value) => update("situation", value)}
              description={flow.situationDescription || ""}
              onDescriptionChange={(value) => update("situationDescription", value)}
            />
          )}
          {step === 2 && (
            flow.situation === "women_children" ? (
              <GuidedCrimeQuestions
                category="women_children"
                subCategory={null}
                details={flow.womenChildrenDetails}
                evidenceFiles={flow.evidenceFiles}
                onSubCategoryChange={() => undefined}
                onDetailsChange={(value) => update("womenChildrenDetails", value)}
                onEvidenceFilesChange={(value) => update("evidenceFiles", value)}
                onComplete={() => { void finishWomenChildren(); }}
              />
            ) : <StepIncidentType value={flow.incidentType} onChange={(value) => update("incidentType", value)} />
          )}
          {step === 3 && (
            flow.incidentType === "other_cyber_crime" ? (
              <StepOtherCrimeDetails
                subCategory={flow.otherCrimeSubCategory}
                details={flow.otherCrimeDetails}
                onSubCategoryChange={(value) => update("otherCrimeSubCategory", value)}
                onDetailsChange={(value) => update("otherCrimeDetails", value)}
                evidenceFiles={flow.evidenceFiles}
                onEvidenceFilesChange={(value) => update("evidenceFiles", value)}
              />
            ) : <StepWhen
              preset={flow.timePreset}
              exactValue={flow.exactValue}
              onPreset={(preset) => {
                const nextExact =
                  preset === "exact"
                    ? flow.exactValue || toDateTimeLocalValue(new Date())
                    : toDateTimeLocalValue(occurredAtFromPreset(preset));
                setFlow((prev) => ({
                  ...prev,
                  timePreset: preset,
                  exactValue: nextExact,
                }));
                setErrorMessage("");
              }}
              onExactChange={(value) => {
                setFlow((prev) => ({
                  ...prev,
                  timePreset: "exact",
                  exactValue: value,
                }));
                setErrorMessage("");
              }}
            />
          )}
          {step === 4 && (
            flow.incidentType === "other_cyber_crime" ? <StepWhen
              preset={flow.timePreset}
              exactValue={flow.exactValue}
              onPreset={(preset) => {
                const nextExact = preset === "exact"
                  ? flow.exactValue || toDateTimeLocalValue(new Date())
                  : toDateTimeLocalValue(occurredAtFromPreset(preset));
                setFlow((prev) => ({ ...prev, timePreset: preset, exactValue: nextExact }));
                setErrorMessage("");
              }}
              onExactChange={(value) => {
                setFlow((prev) => ({ ...prev, timePreset: "exact", exactValue: value }));
                setErrorMessage("");
              }}
            /> : <StepAmount
              amount={flow.amount}
              paymentMethod={flow.paymentMethod}
              onAmountChange={(value) => update("amount", value)}
              onPaymentMethodChange={(value) => update("paymentMethod", value)}
            />
          )}
          {step === 5 && (
            <StepTransactionId
              value={flow.transactionId}
              onChange={(value) => update("transactionId", value)}
              status={flow.transactionStatus}
              onStatusChange={(value) => update("transactionStatus", value)}
              ongoing={flow.ongoingRisk}
              onOngoingChange={(value) => update("ongoingRisk", value)}
            />
          )}

          {busy && (
            <div className="mt-6">
              <LoadingState
                message={
                  step === 5
                    ? "Working out what you should do first…"
                    : "Starting your incident…"
                }
              />
            </div>
          )}

          {errorMessage && !busy && (
            <div className="mt-6">
              <ErrorState
                message={errorMessage}
                onRetry={handleNext}
              />
            </div>
          )}

          {!(step === 2 && flow.situation === "women_children") && (
            <FlowNav
              onBack={step > 1 ? handleBack : undefined}
              onNext={handleNext}
              nextLabel={step === 5 ? "See what to do now" : "Continue"}
              busy={busy}
            />
          )}
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
