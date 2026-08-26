import { OptionCard } from "@/components/option-card";
import type { ReactNode } from "react";
import {
  OTHER_CRIME_OPTIONS,
  type OtherCrimeSubCategory,
} from "@/types/incident";

export type OtherCrimeDetails = Record<string, string | boolean>;

const OCCURRED_ON_OPTIONS = [
  "SMS",
  "Call",
  "Email",
  "Website",
  "App",
  "Social media",
  "Other",
];

const ONLINE_SOCIAL_SUBCATEGORIES = [
  "Cyber Bullying/Stalking/Sexting",
  "E-Mail Phishing",
  "Email Hacking",
  "Fake/Impersonating Profile",
  "Impersonating Email",
  "Online Job Fraud",
  "Online Matrimonial Fraud",
  "Profile Hacking",
  "Provocative Speech",
  "Intimidating Email",
];

const HACKING_SUBCATEGORIES = [
  "Unauthorized Access/Data Breach",
  "Website Related/Defacement",
];

function TextField({
  label,
  value,
  onChange,
  required = false,
  multiline = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  multiline?: boolean;
}) {
  const className = "mt-2 w-full rounded-md border border-line2 bg-white px-3 py-3 text-[15px] text-ink";
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">
        {label}
        {required && <span className="text-urgent"> *</span>}
      </span>
      {multiline ? (
        <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={4} className={className} />
      ) : (
        <input value={value} onChange={(event) => onChange(event.target.value)} className={className} />
      )}
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">
        {label}
        {required && <span className="text-urgent"> *</span>}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 h-12 w-full rounded-md border border-line2 bg-white px-3 text-[15px] text-ink"
      >
        <option value="">Select</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function FieldGroup({ children }: { children: ReactNode }) {
  return <div className="mt-8 grid gap-5 rounded-lg border border-line bg-surface px-5 py-5">{children}</div>;
}

interface StepOtherCrimeDetailsProps {
  subCategory: OtherCrimeSubCategory | null;
  details: OtherCrimeDetails;
  onSubCategoryChange: (value: OtherCrimeSubCategory) => void;
  onDetailsChange: (details: OtherCrimeDetails) => void;
  evidenceFiles: File[];
  onEvidenceFilesChange: (files: File[]) => void;
}

export function StepOtherCrimeDetails({
  subCategory,
  details,
  onSubCategoryChange,
  onDetailsChange,
  evidenceFiles,
  onEvidenceFilesChange,
}: StepOtherCrimeDetailsProps) {
  function setDetail(key: string, value: string | boolean) {
    onDetailsChange({ ...details, [key]: value });
  }

  const socialSub = String(details.social_media_sub_category ?? "");
  const hackingSub = String(details.hacking_sub_category ?? "");
  const lostMoney = details.lost_money === true;

  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">Which other cyber crime fits best?</h1>
      <div role="radiogroup" aria-label="Other cyber crime sub-category" className="mt-8 flex flex-col gap-3">
        {OTHER_CRIME_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            selected={subCategory === option.id}
            onSelect={() => onSubCategoryChange(option.id)}
            label={option.label}
            description={option.description}
          />
        ))}
      </div>

      {subCategory && (
        <FieldGroup>
          <TextField label="Date/time of incident" value={String(details.incident_date_time ?? "")} onChange={(value) => setDetail("incident_date_time", value)} required />
          <TextField label="Reason for delay" value={String(details.reason_for_delay ?? "")} onChange={(value) => setDetail("reason_for_delay", value)} />
          <SelectField label="Where did it occur" value={String(details.occurred_on ?? "")} onChange={(value) => setDetail("occurred_on", value)} options={OCCURRED_ON_OPTIONS} required />

          {subCategory === "online_social_media" && (
            <>
              <SelectField label="Sub-category" value={socialSub} onChange={(value) => setDetail("social_media_sub_category", value)} options={ONLINE_SOCIAL_SUBCATEGORIES} required />
              {(socialSub === "Impersonating Email" || socialSub === "Intimidating Email") && (
                <>
                  <TextField label="Service Provider" value={String(details.service_provider ?? "")} onChange={(value) => setDetail("service_provider", value)} required />
                  <TextField label="Full Header of Email" value={String(details.full_header_of_email ?? "")} onChange={(value) => setDetail("full_header_of_email", value)} required multiline />
                </>
              )}
            </>
          )}

          {(subCategory === "ransomware" || subCategory === "cryptocurrency") && (
            <>
              <TextField label="Bitcoin address/details" value={String(details.bitcoin_details ?? "")} onChange={(value) => setDetail("bitcoin_details", value)} required multiline />
              <TextField label="Darknet ID/details" value={String(details.darknet_details ?? "")} onChange={(value) => setDetail("darknet_details", value)} multiline />
            </>
          )}

          {subCategory === "hacking" && (
            <>
              <SelectField label="Sub-category" value={hackingSub} onChange={(value) => setDetail("hacking_sub_category", value)} options={HACKING_SUBCATEGORIES} required />
              {hackingSub === "Unauthorized Access/Data Breach" && (
                <SelectField label="Mode of communication" value={String(details.mode_of_communication ?? "")} onChange={(value) => setDetail("mode_of_communication", value)} options={["Email", "Account", "Server", "Other"]} required />
              )}
              {hackingSub === "Website Related/Defacement" && (
                <>
                  <TextField label="Website Domain name" value={String(details.website_domain_name ?? "")} onChange={(value) => setDetail("website_domain_name", value)} required />
                  <TextField label="Other Additional Details" value={String(details.other_additional_details ?? "")} onChange={(value) => setDetail("other_additional_details", value)} required multiline />
                </>
              )}
            </>
          )}

          {subCategory === "online_trafficking" && (
            <>
              <TextField label="What is being trafficked" value={String(details.trafficked_item ?? "")} onChange={(value) => setDetail("trafficked_item", value)} multiline />
              <TextField label="Social Media Used" value={String(details.social_media_used ?? "")} onChange={(value) => setDetail("social_media_used", value)} required />
              <TextField label="Darknet ID/details" value={String(details.darknet_details ?? "")} onChange={(value) => setDetail("darknet_details", value)} multiline />
            </>
          )}

          {subCategory === "online_gambling" && (
            <>
              <TextField label="Gambling is related with" value={String(details.gambling_related_with ?? "")} onChange={(value) => setDetail("gambling_related_with", value)} required />
              <label className="flex items-center gap-3 text-sm font-medium text-ink">
                <input type="checkbox" checked={lostMoney} onChange={(event) => setDetail("lost_money", event.target.checked)} className="h-5 w-5 rounded border-line2" />
                Have you lost money?
              </label>
              {lostMoney && (
                <>
                  <TextField label="Transaction ID" value={String(details.transaction_id ?? "")} onChange={(value) => setDetail("transaction_id", value)} required />
                  <TextField label="Date/Time of transaction" value={String(details.transaction_date_time ?? "")} onChange={(value) => setDetail("transaction_date_time", value)} required />
                  <TextField label="Bank Name paid from" value={String(details.bank_name_paid_from ?? "")} onChange={(value) => setDetail("bank_name_paid_from", value)} required />
                  <TextField label="Account No. paid from" value={String(details.account_no_paid_from ?? "")} onChange={(value) => setDetail("account_no_paid_from", value)} required />
                  <TextField label="Amount Paid" value={String(details.amount_paid ?? "")} onChange={(value) => setDetail("amount_paid", value)} required />
                  <TextField label="Bank/Account paid to" value={String(details.bank_account_paid_to ?? "")} onChange={(value) => setDetail("bank_account_paid_to", value)} required />
                  <TextField label="Merchant/Gateway details" value={String(details.merchant_gateway_details ?? "")} onChange={(value) => setDetail("merchant_gateway_details", value)} required />
                </>
              )}
            </>
          )}

          {subCategory === "any_other" && (
            <TextField label="Provide Other Crime Details" value={String(details.other_crime_details ?? "")} onChange={(value) => setDetail("other_crime_details", value)} required multiline />
          )}

          <label className="block">
            <span className="text-sm font-medium text-ink">Evidence upload</span>
            <input
              type="file"
              multiple
              onChange={(event) => onEvidenceFilesChange(Array.from(event.target.files ?? []))}
              className="mt-2 w-full rounded-md border border-line2 bg-white px-3 py-3 text-[15px] text-ink"
            />
            {evidenceFiles.length > 0 && (
              <p className="mt-2 text-sm text-ink-muted">{evidenceFiles.length} file(s) selected</p>
            )}
          </label>
          <TextField label="Additional details" value={String(details.additional_details ?? "")} onChange={(value) => setDetail("additional_details", value)} multiline />
        </FieldGroup>
      )}
    </div>
  );
}
