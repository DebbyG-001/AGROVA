"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button, Logo, Tag } from "@/components/ui";
import { ChoiceGroup, FormHeading, TextField } from "@/components/form";
import {
  FARM_SIZES,
  FARM_TYPES,
  LIVESTOCK_TYPES,
  NIGERIAN_STATES,
  emptySetup,
  validateStep,
  type Errors,
  type FarmSetup,
  type LivestockKey,
} from "@/lib/farm-setup";
import { saveFarm } from "@/services/farm";

const STEPS = ["You", "Your farm", "Livestock", "Review"];

export default function Onboarding() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [data, setData] = useState<FarmSetup>(emptySetup);
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const heading = useRef<HTMLDivElement>(null);

  // Move focus to the new step so keyboard and screen-reader users know the page changed.
  useEffect(() => {
    heading.current?.focus();
  }, [step]);

  const set = <K extends keyof FarmSetup>(k: K, v: FarmSetup[K]) => {
    setData((d) => ({ ...d, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
  };

  const toggleLivestock = (k: LivestockKey) => {
    setData((d) => {
      const next = { ...d.livestock };
      if (k in next) delete next[k];
      else next[k] = "";
      return { ...d, livestock: next };
    });
    setErrors((e) => ({ ...e, livestock: undefined }));
  };

  function next() {
    const e = validateStep(step, data);
    setErrors(e);
    if (Object.keys(e).length === 0) setStep((s) => s + 1);
  }

  async function finish() {
    setSaving(true);
    setSaveError("");
    try {
      await saveFarm(data);
      router.push("/app");
    } catch {
      setSaveError("We couldn't save your farm. Please try again.");
      setSaving(false);
    }
  }

  const label = (list: readonly { key: string; label: string }[], key: string) =>
    list.find((o) => o.key === key)?.label ?? "";

  return (
    <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[22rem_minmax(0,1fr)]">
      {/* Desktop side panel */}
      <aside className="hidden flex-col justify-between bg-forest p-8 text-lime lg:flex">
        <div>
          <Link href="/" aria-label="Agrova home" className="inline-flex min-h-11 items-center">
            <Logo light />
          </Link>
          <ol className="mt-14 space-y-5" aria-label="Setup progress">
            {STEPS.map((s, i) => (
              <li
                key={s}
                aria-current={i === step ? "step" : undefined}
                className={`flex items-center gap-4 ${i === step ? "" : "opacity-55"}`}
              >
                <span
                  className={`grid size-9 place-items-center rounded-full border border-lime font-mono text-sm ${
                    i < step ? "bg-lime text-forest" : i === step ? "bg-lime/15" : ""
                  }`}
                >
                  {i < step ? "✓" : i + 1}
                </span>
                <span className="label">{s}</span>
              </li>
            ))}
          </ol>
        </div>
        <p className="max-w-[16rem] text-lime/80">
          You won&apos;t fill forms like this again. After setup, just tell Agro AI what happens on your farm.
        </p>
      </aside>

      <div className="flex min-h-dvh min-w-0 flex-col">
        {/* Mobile top bar */}
        <header className="bg-lime px-5 py-3 lg:hidden">
          <div className="flex items-center justify-between">
            <Link href="/" aria-label="Agrova home" className="inline-flex min-h-11 items-center">
              <Logo />
            </Link>
            <span className="label">
              Step {step + 1} of {STEPS.length}
            </span>
          </div>
          <div
            className="mt-3 h-1.5 rounded-full bg-forest/15"
            role="progressbar"
            aria-valuemin={1}
            aria-valuemax={STEPS.length}
            aria-valuenow={step + 1}
            aria-label="Setup progress"
          >
            <div
              className="h-1.5 rounded-full bg-forest transition-all"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
        </header>

        <main className="flex-1 px-5 py-8 md:px-10 lg:px-16 lg:py-14">
          <div className="mx-auto w-full max-w-2xl">
            <div ref={heading} tabIndex={-1} className="outline-none">
              <p className="label mb-3">
                <Tag>
                  Step {step + 1} of {STEPS.length}
                </Tag>
              </p>

              {step === 0 && <FormHeading sub="Just the basics. We'll use your name when Agro AI talks to you.">Welcome to Agrova</FormHeading>}
              {step === 1 && <FormHeading sub="This helps Agrova give advice that fits your kind of farm.">Tell us about your farm</FormHeading>}
              {step === 2 && <FormHeading sub="Pick everything you keep. You can add or change this any time.">What do you keep?</FormHeading>}
              {step === 3 && <FormHeading sub="Check everything looks right, then create your farm.">Almost done</FormHeading>}
            </div>

            <form
              noValidate
              onSubmit={(e) => {
                e.preventDefault();
                if (step < STEPS.length - 1) next();
                else finish();
              }}
              className="space-y-8"
            >
              {step === 0 && (
                <div className="space-y-6">
                  <TextField
                    id="ownerName"
                    label="Your name"
                    value={data.ownerName}
                    onChange={(v) => set("ownerName", v)}
                    error={errors.ownerName}
                    autoComplete="name"
                    placeholder="e.g. Adewale Johnson"
                  />
                  <TextField
                    id="phone"
                    label="Phone number"
                    optional
                    value={data.phone}
                    onChange={(v) => set("phone", v)}
                    error={errors.phone}
                    hint="Used to link WhatsApp later."
                    type="tel"
                    inputMode="tel"
                    autoComplete="tel"
                    placeholder="0803 123 4567"
                  />
                </div>
              )}

              {step === 1 && (
                <div className="space-y-8">
                  <TextField
                    id="farmName"
                    label="Farm name"
                    value={data.farmName}
                    onChange={(v) => set("farmName", v)}
                    error={errors.farmName}
                    placeholder="e.g. Dons Farm"
                  />
                  <TextField
                    id="location"
                    label="Location"
                    value={data.location}
                    onChange={(v) => set("location", v)}
                    error={errors.location}
                    list="states"
                    autoComplete="address-level1"
                    hint="Choose a state or type your town."
                    placeholder="e.g. Ogun"
                  />
                  <datalist id="states">
                    {NIGERIAN_STATES.map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                  <ChoiceGroup
                    name="farmType"
                    legend="What kind of farm is it?"
                    options={FARM_TYPES}
                    value={data.farmType}
                    onChange={(v) => set("farmType", v)}
                    error={errors.farmType}
                  />
                  <ChoiceGroup
                    name="size"
                    legend="How big is it?"
                    options={FARM_SIZES}
                    value={data.size}
                    onChange={(v) => set("size", v)}
                    error={errors.size}
                    columns="sm:grid-cols-3"
                  />
                </div>
              )}

              {step === 2 && (
                <fieldset aria-describedby={errors.livestock ? "livestock-err" : undefined}>
                  <legend className="sr-only">Livestock you keep</legend>
                  <ul className="grid gap-3 sm:grid-cols-2">
                    {LIVESTOCK_TYPES.map((t) => {
                      const on = t.key in data.livestock;
                      return (
                        <li
                          key={t.key}
                          className={`rounded-2xl border p-4 transition-colors ${
                            on ? "border-forest bg-lime" : "border-forest/20 bg-white"
                          }`}
                        >
                          <label className="flex cursor-pointer items-start gap-3 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-4 has-[:focus-visible]:outline-leaf">
                            <input
                              type="checkbox"
                              checked={on}
                              onChange={() => toggleLivestock(t.key)}
                              className="mt-1 size-5 accent-forest"
                            />
                            <span>
                              <span className="block font-bold">{t.label}</span>
                              <span className="mt-1 block text-sm text-forest/75">{t.hint}</span>
                            </span>
                          </label>
                          {on && (
                            <div className="mt-3 pl-8">
                              <label htmlFor={`count-${t.key}`} className="mb-1 block text-sm">
                                How many? <span className="opacity-60">(optional)</span>
                              </label>
                              <input
                                id={`count-${t.key}`}
                                inputMode="numeric"
                                value={data.livestock[t.key] ?? ""}
                                onChange={(e) =>
                                  setData((d) => ({
                                    ...d,
                                    livestock: { ...d.livestock, [t.key]: e.target.value.replace(/\D/g, "") },
                                  }))
                                }
                                placeholder="e.g. 200"
                                className="min-h-11 w-32 rounded-xl border border-forest/30 bg-white px-3"
                              />
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                  {errors.livestock && (
                    <p id="livestock-err" role="alert" className="mt-3 text-sm font-bold text-critical">
                      {errors.livestock}
                    </p>
                  )}
                </fieldset>
              )}

              {step === 3 && (
                <div className="space-y-4">
                  <ReviewCard title="You" onEdit={() => setStep(0)}>
                    <Row k="Name" v={data.ownerName} />
                    <Row k="Phone" v={data.phone || "Not added"} />
                  </ReviewCard>
                  <ReviewCard title="Farm" onEdit={() => setStep(1)}>
                    <Row k="Name" v={data.farmName} />
                    <Row k="Location" v={data.location} />
                    <Row k="Type" v={label(FARM_TYPES, data.farmType)} />
                    <Row k="Size" v={label(FARM_SIZES, data.size)} />
                  </ReviewCard>
                  <ReviewCard title="Livestock" onEdit={() => setStep(2)}>
                    {(Object.keys(data.livestock) as LivestockKey[]).map((k) => (
                      <Row
                        key={k}
                        k={label(LIVESTOCK_TYPES, k)}
                        v={data.livestock[k] ? Number(data.livestock[k]).toLocaleString("en-NG") : "Count not added"}
                      />
                    ))}
                  </ReviewCard>
                  {saveError && (
                    <p role="alert" className="text-sm font-bold text-critical">
                      {saveError}
                    </p>
                  )}
                </div>
              )}

              <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
                {step > 0 ? (
                  <Button type="button" variant="outline" onClick={() => setStep((s) => s - 1)} className="sm:w-auto">
                    Back
                  </Button>
                ) : (
                  <span />
                )}
                <Button type="submit" variant="forest" disabled={saving} className="!min-h-14 !px-9 !text-base">
                  {step < STEPS.length - 1 ? "Continue" : saving ? "Creating…" : "Create my farm"}
                </Button>
              </div>
            </form>

            {step === 0 && (
              <div className="mt-10 flex flex-col gap-3 border-t border-forest/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-forest/80">
                  Presenting or just exploring? Skip setup and open a ready-made farm with sample data.
                </p>
                <Button href="/app" variant="outline" className="shrink-0 whitespace-nowrap">
                  Use demo account
                </Button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function ReviewCard({ title, onEdit, children }: { title: string; onEdit: () => void; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-forest/10 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="label">
          <Tag>{title}</Tag>
        </h2>
        <button type="button" onClick={onEdit} className="label min-h-9 underline underline-offset-4">
          Edit
        </button>
      </div>
      <dl className="space-y-2">{children}</dl>
    </section>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-forest/70">{k}</dt>
      <dd className="text-right font-bold">{v}</dd>
    </div>
  );
}
