import { useState } from "react";
import { Check } from "lucide-react";

import { OptionCard } from "@/components/option-card";
import { type OtherCrimeSubCategory, type TopLevelCrimeCategory } from "@/types/incident";

export type GuidedCrimeDetails = Record<string, string | boolean | string[]>;

type Props = {
  category: Exclude<TopLevelCrimeCategory, "financial_fraud">;
  subCategory: OtherCrimeSubCategory | null;
  details: GuidedCrimeDetails;
  evidenceFiles: File[];
  onSubCategoryChange: (value: OtherCrimeSubCategory) => void;
  onDetailsChange: (details: GuidedCrimeDetails) => void;
  onEvidenceFilesChange: (files: File[]) => void;
  onComplete: (complete: boolean) => void;
};

type Question = { key: string; prompt: string; help?: string; kind?: "text" | "long" | "choice" | "file"; options?: string[]; required?: boolean };

function questionSet(category: Props["category"], subCategory: OtherCrimeSubCategory | null, details: GuidedCrimeDetails): Question[] {
  if (category === "women_children") {
    return [
      { key: "incident_subtype", prompt: "What happened?", kind: "choice", options: ["Online harassment", "Cyberstalking", "Threats or blackmail", "Intimate/private content shared or threatened", "Sexual harassment", "Child exploitation / inappropriate contact", "Fake profile / impersonation", "Other"], required: true },
      { key: "immediate_danger", prompt: "Is anyone in immediate physical danger?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true },
      { key: "affected_person_type", prompt: "Who is affected?", kind: "choice", options: ["Me", "A child", "Another woman", "Another person", "I'm reporting on behalf of someone else"], required: true },
      { key: "platform", prompt: "Where did this happen?", kind: "choice", options: ["WhatsApp", "Instagram", "Facebook", "Telegram", "YouTube", "Dating app", "Email", "Website", "Phone/SMS", "Other"], required: true },
      { key: "content_still_online", prompt: "Is the content/profile/message still available?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true },
      { key: "threat_or_blackmail", prompt: "Are you being threatened, blackmailed, or pressured?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true },
      { key: "evidence_types", prompt: "Do you have evidence of what happened?", kind: "choice", options: ["Screenshots", "Messages/chats", "Profile/account details", "Photos/videos", "URLs", "Other evidence", "I don't have evidence"], required: true },
      { key: "incident_time", prompt: "When did this happen?", kind: "choice", options: ["Just now", "Within the last 24 hours", "Within the last week", "Within the last month", "More than a month ago", "I'm not sure"], required: true },
    ];
  }

  const questions: Question[] = [
    { key: "incident_subtype", prompt: "What happened?", kind: "choice", options: ["My account was hacked", "Someone impersonated me", "Phishing / suspicious link", "Malware / suspicious software", "Cyberstalking or harassment", "Fake website / online scam", "Data or personal information was exposed", "Someone is threatening me", "Other"], required: true },
    { key: "account_type", prompt: "Which account or service is affected?", kind: "choice", options: ["Email", "Social media", "Banking/financial account", "Government account", "Shopping account", "Messaging app", "Website/account", "Device", "Other", "Not applicable"], required: true },
    { key: "account_access", prompt: "Do you still have access to the affected account or device?", kind: "choice", options: ["Yes", "No", "I'm not sure", "Not applicable"], required: true },
    { key: "attacker_active", prompt: "Is someone currently using or controlling the account?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true },
    { key: "sensitive_information_exposed", prompt: "Could personal or sensitive information have been exposed?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true },
  ];
  if (String(details.incident_subtype).toLowerCase().includes("phishing")) questions.push({ key: "credentials_entered", prompt: "Did you enter any information after opening the link?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true });
  if (String(details.incident_subtype).toLowerCase().includes("malware")) questions.push({ key: "device_behaving_unusually", prompt: "Is the device behaving unusually?", kind: "choice", options: ["Yes", "No", "I'm not sure"], required: true });
  questions.push({ key: "incident_time", prompt: "When did this happen?", kind: "choice", options: ["Just now", "Within the last 24 hours", "Within the last week", "Within the last month", "More than a month ago", "I'm not sure"], required: true });
  questions.push({ key: "evidence_types", prompt: "Do you have evidence of what happened?", kind: "choice", options: ["Screenshots", "Emails", "Messages", "URLs", "Account/profile information", "Device information", "Other", "No evidence"], required: true });
  return questions;
}

const QUESTION_LABELS: Record<string, string> = {
  incident_subtype: "What happened",
  immediate_danger: "Safety",
  affected_person_type: "Who is affected",
  platform: "Platform",
  content_still_online: "Still online",
  threat_or_blackmail: "Threats",
  account_type: "Account or service",
  account_access: "Access",
  attacker_active: "Active control",
  sensitive_information_exposed: "Sensitive information",
  credentials_entered: "Information entered",
  device_behaving_unusually: "Device status",
  incident_time: "When",
  evidence_types: "Evidence",
};

export function guidedQuestionLabels(
  category: Props["category"],
  subCategory: OtherCrimeSubCategory | null,
  details: GuidedCrimeDetails,
): string[] {
  return questionSet(category, subCategory, details).map((question) => QUESTION_LABELS[question.key] ?? "Question");
}

export function GuidedCrimeQuestions({ category, subCategory, details, evidenceFiles, onSubCategoryChange, onDetailsChange, onEvidenceFilesChange, onComplete, onProgress }: Props & { onProgress?: (index: number) => void }) {
  const questions = questionSet(category, subCategory, details);
  const [index, setIndex] = useState(0);
  const question = questions[index];
  const rawValue = details[question.key];
  const value = Array.isArray(rawValue) ? rawValue.join(", ") : String(rawValue ?? "");

  function setValue(next: string | boolean) {
    onDetailsChange({ ...details, [question.key]: next });
  }

  function toggleValue(option: string) {
    const selected = Array.isArray(rawValue) ? rawValue : [];
    onDetailsChange({ ...details, [question.key]: selected.includes(option) ? selected.filter((item) => item !== option) : [...selected, option] });
  }

  function next() {
    if (question.required && !value.trim()) return;
    if (index === questions.length - 1) {
      onComplete(true);
      return;
    }
    const nextIndex = index + 1;
    setIndex(nextIndex);
    onProgress?.(nextIndex);
  }

  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Question {index + 1} of {questions.length}</p>
      <h1 className="mt-3 font-display text-3xl text-ink sm:text-4xl">{question.prompt}</h1>
      {question.help && <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">{question.help}</p>}
      <div className="mt-8">
        {question.kind === "choice" && <div className="flex flex-col gap-3">{question.options?.map((option) => <OptionCard key={option} selected={question.key === "evidence_types" ? (Array.isArray(rawValue) && rawValue.includes(option)) : value === option} onSelect={() => question.key === "evidence_types" ? toggleValue(option) : setValue(option)} label={option} />)}</div>}
        {(question.kind === "text" || !question.kind || question.kind === "long") && (question.kind === "long" ? <textarea value={value} onChange={(event) => setValue(event.target.value)} rows={5} className="w-full rounded-md border border-line2 bg-white px-4 py-3 text-[15px] text-ink" /> : <input value={value} onChange={(event) => setValue(event.target.value)} className="w-full rounded-md border border-line2 bg-white px-4 py-3 text-[15px] text-ink" />)}
        <button type="button" onClick={next} disabled={question.required && !value.trim()} className="mt-6 inline-flex items-center gap-2 rounded-md bg-ink px-5 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40">{index === questions.length - 1 ? <Check size={16} aria-hidden="true" /> : null}{index === questions.length - 1 ? "Create complaint draft" : "Continue"}</button>
      </div>
    </div>
  );
}
