"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Card, Tag } from "@/components/ui";
import { ChoiceGroup, SelectField, TextArea, TextField } from "@/components/form";
import {
  DRINKING,
  ONSET,
  SPECIES,
  VACCINATED,
  emptyHealthForm,
  validateHealth,
  type HealthAssessment,
  type HealthErrors,
  type HealthForm,
  type RiskLevel,
} from "@/lib/health";
import { ApiError } from "@/lib/api";
import { assessHealth } from "@/services/health";

const RISK_STYLE: Record<RiskLevel, string> = {
  LOW: "bg-lime text-forest",
  MEDIUM: "bg-warn/15 text-warn",
  HIGH: "bg-critical/15 text-critical",
};

export default function HealthAssistant() {
  const [form, setForm] = useState<HealthForm>(emptyHealthForm);
  const [errors, setErrors] = useState<HealthErrors>({});
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState("");
  const [result, setResult] = useState<HealthAssessment | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Free the temporary photo preview URL when it changes or the page closes.
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const set = <K extends keyof HealthForm>(k: K, v: HealthForm[K]) => {
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
  };

  function pickPhoto(file: File | null) {
    setPhoto(file);
    setPreview(file ? URL.createObjectURL(file) : null);
    setErrors((e) => ({ ...e, photo: undefined }));
  }

  function removePhoto() {
    pickPhoto(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function submit() {
    const e = validateHealth(form, photo);
    setErrors(e);
    if (Object.keys(e).length > 0) {
      document.getElementById(Object.keys(e)[0])?.focus();
      return;
    }
    setBusy(true);
    setFailed("");
    setResult(null); // never leave an old assessment on screen next to a new question
    try {
      setResult(await assessHealth(form, photo));
      requestAnimationFrame(() => resultRef.current?.focus());
    } catch (err) {
      setFailed(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function startOver() {
    setForm(emptyHealthForm);
    setErrors({});
    setResult(null);
    removePhoto();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label mb-2"><Tag>Health Assistant</Tag></p>
        <h1 className="h-display text-3xl lg:text-5xl">Check animal health</h1>
        <p className="mt-4 max-w-2xl text-forest/80">
          Tell us what you are seeing. You get a risk level and safe next steps. This is decision support, not a
          vet diagnosis.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] lg:items-start lg:gap-8">
        <form
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          className="space-y-7 rounded-2xl border border-forest/10 bg-white p-5 md:p-7"
        >
          <SelectField
            id="species"
            label="Which animal?"
            value={form.species}
            onChange={(v) => set("species", v)}
            options={SPECIES}
            error={errors.species}
          />

          <TextArea
            id="symptoms"
            label="What are you seeing?"
            value={form.symptoms}
            onChange={(v) => set("symptoms", v)}
            error={errors.symptoms}
            hint="For example: coughing, not eating well, watery droppings."
            placeholder="Describe the signs in your own words"
          />

          <div className="grid gap-5 sm:grid-cols-3">
            <TextField
              id="affected"
              label="How many sick?"
              value={form.affected}
              onChange={(v) => set("affected", v.replace(/\D/g, ""))}
              error={errors.affected}
              inputMode="numeric"
              placeholder="e.g. 12"
            />
            <TextField
              id="total"
              label="Out of how many?"
              optional
              value={form.total}
              onChange={(v) => set("total", v.replace(/\D/g, ""))}
              error={errors.total}
              inputMode="numeric"
              placeholder="e.g. 500"
            />
            <TextField
              id="deaths"
              label="How many died?"
              value={form.deaths}
              onChange={(v) => set("deaths", v.replace(/\D/g, ""))}
              error={errors.deaths}
              inputMode="numeric"
              placeholder="0"
            />
          </div>

          <ChoiceGroup
            name="onset"
            legend="When did it start?"
            options={ONSET}
            value={form.onset}
            onChange={(v) => set("onset", v)}
            error={errors.onset}
            columns="sm:grid-cols-3"
          />
          <ChoiceGroup
            name="drinking"
            legend="Are they drinking?"
            options={DRINKING}
            value={form.drinking}
            onChange={(v) => set("drinking", v)}
            error={errors.drinking}
          />
          <ChoiceGroup
            name="vaccinated"
            legend="Recently vaccinated?"
            options={VACCINATED}
            value={form.vaccinated}
            onChange={(v) => set("vaccinated", v)}
            columns="sm:grid-cols-3"
          />

          <div>
            <label htmlFor="photo" className="mb-2 block font-bold">
              Add a photo <span className="label ml-2 font-normal opacity-60">Optional</span>
            </label>
            <input
              ref={fileRef}
              id="photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              aria-invalid={errors.photo ? true : undefined}
              aria-describedby={errors.photo ? "photo-err" : "photo-hint"}
              onChange={(e) => pickPhoto(e.target.files?.[0] ?? null)}
              className="block w-full text-sm file:mr-4 file:min-h-11 file:cursor-pointer file:rounded-full file:border file:border-forest file:bg-lime file:px-5 file:font-mono file:text-xs file:uppercase"
            />
            {errors.photo ? (
              <p id="photo-err" role="alert" className="mt-2 text-sm font-bold text-critical">
                {errors.photo}
              </p>
            ) : (
              <p id="photo-hint" className="mt-2 text-sm text-forest/70">
                JPG, PNG or WebP, up to 5 MB. Show the affected area in good light.
              </p>
            )}
            {preview && !errors.photo && (
              <div className="mt-3 flex items-center gap-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={preview} alt="Your uploaded animal photo" className="size-24 rounded-xl object-cover" />
                <button type="button" onClick={removePhoto} className="label min-h-11 underline underline-offset-4">
                  Remove photo
                </button>
              </div>
            )}
          </div>

          {failed && (
            <p role="alert" className="text-sm font-bold text-critical">
              {failed}
            </p>
          )}

          <Button type="submit" variant="forest" disabled={busy} className="w-full !min-h-14 !text-base">
            {busy ? "Checking…" : "Check health"}
          </Button>
        </form>

        <div ref={resultRef} tabIndex={-1} className="outline-none lg:sticky lg:top-6" aria-live="polite">
          {!result ? (
            <Card className="!p-6">
              <p className="label mb-3"><Tag>Your assessment</Tag></p>
              <p className="text-forest/80">
                Fill in the form and your risk level and next steps will appear here.
              </p>
              <p className="mt-4 text-sm text-forest/70">
                Serious signs like trouble breathing, bloody droppings or sudden deaths need a vet straight away,
                even before you finish this form.
              </p>
            </Card>
          ) : (
            <Result r={result} onReset={startOver} />
          )}
        </div>
      </div>
    </div>
  );
}

function Result({ r, onReset }: { r: HealthAssessment; onReset: () => void }) {
  return (
    <div className="space-y-4">
      {r.source === "demo" && (
        <p role="note" className="rounded-2xl border border-warn/40 bg-white p-4 text-sm">
          <b>Demo assessment.</b> This uses simple rules, not Agro AI yet. It shows the layout and gives general
          safe steps only.
        </p>
      )}

      <Card className="!p-6">
        <p className="label mb-3"><Tag>Health risk</Tag></p>
        <span className={`label inline-block rounded-full px-4 py-1.5 text-base ${RISK_STYLE[r.risk]}`}>
          {r.risk}
        </span>

        <Section title="What you told us" items={r.observed} />
        <Section
          title="Possible concerns"
          items={r.possibleConcerns}
          empty="Agro AI will list possible concerns here once it is connected."
        />
        <Section title="Do now" items={r.nextSteps} numbered />

        <div className="mt-6 rounded-xl bg-lime p-4">
          <p className="label mb-1">Call the vet</p>
          <p>{r.callVet}</p>
        </div>

        {r.photoNote && <p className="mt-4 text-sm text-forest/75">{r.photoNote}</p>}

        <p className="mt-6 border-t border-forest/10 pt-4 text-sm text-forest/70">
          Agrova provides AI-assisted decision support and does not replace professional veterinary diagnosis.
        </p>
      </Card>

      <Button type="button" variant="outline" onClick={onReset} className="w-full">
        Check another
      </Button>
    </div>
  );
}

function Section({
  title,
  items,
  numbered = false,
  empty,
}: {
  title: string;
  items: string[];
  numbered?: boolean;
  empty?: string;
}) {
  if (items.length === 0 && !empty) return null;
  const List = numbered ? "ol" : "ul";
  return (
    <div className="mt-6">
      <h2 className="label mb-3">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-forest/70">{empty}</p>
      ) : (
        <List className={`space-y-2 pl-5 ${numbered ? "list-decimal" : "list-disc"} marker:text-leaf`}>
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </List>
      )}
    </div>
  );
}
