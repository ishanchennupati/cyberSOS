"use client";

import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { ErrorState } from "@/components/error-state";
import { FlowNav } from "@/components/flow-nav";
import { LoadingState } from "@/components/loading-state";
import { ProgressSteps } from "@/components/progress-steps";
import { StepAmount } from "@/components/steps/step-amount";
import { StepIncidentType } from "@/components/steps/step-incident-type";
import { StepOtherCrimeDetails } from "@/components/steps/step-other-crime-details";
import { StepSituation } from "@/components/steps/step-situation";
import { StepTransactionId } from "@/components/steps/step-transaction-id";
import { StepWhen } from "@/components/steps/step-when";
import { GuidedCrimeQuestions } from "@/components/steps/guided-crime-questions";
import { STEPS, useIncidentFlow } from "@/features/incident-intake/use-incident-flow";

function IncidentStartFlow() {
  const { step, flow, errorMessage, busy, update, handleNext, handleBack,
    finishWomenChildren, onTimePreset, onExactTime } = useIncidentFlow();

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
              onPreset={onTimePreset}
              onExactChange={onExactTime}
            />
          )}
          {step === 4 && (
            flow.incidentType === "other_cyber_crime" ? <StepWhen
              preset={flow.timePreset}
              exactValue={flow.exactValue}
              onPreset={onTimePreset}
              onExactChange={onExactTime}
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
