import type { ReactNode } from "react";

const inputCls =
  "min-h-12 w-full rounded-2xl border bg-white px-4 text-base placeholder:text-forest/40";

export function TextField({
  id,
  label,
  value,
  onChange,
  error,
  hint,
  list,
  type = "text",
  autoComplete,
  inputMode,
  placeholder,
  optional = false,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  hint?: string;
  list?: string;
  type?: string;
  autoComplete?: string;
  inputMode?: "text" | "numeric" | "tel" | "email";
  placeholder?: string;
  optional?: boolean;
}) {
  const describedBy = [error && `${id}-err`, hint && `${id}-hint`].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={id} className="mb-2 block font-bold">
        {label}
        {optional && <span className="label ml-2 font-normal opacity-60">Optional</span>}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        list={list}
        autoComplete={autoComplete}
        inputMode={inputMode}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        onChange={(e) => onChange(e.target.value)}
        className={`${inputCls} ${error ? "border-critical" : "border-forest/20"}`}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-2 text-sm text-forest/70">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} role="alert" className="mt-2 text-sm font-bold text-critical">
          {error}
        </p>
      )}
    </div>
  );
}

export function TextArea({
  id,
  label,
  value,
  onChange,
  error,
  hint,
  placeholder,
  rows = 4,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  hint?: string;
  placeholder?: string;
  rows?: number;
}) {
  const describedBy = [error && `${id}-err`, hint && `${id}-hint`].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={id} className="mb-2 block font-bold">
        {label}
      </label>
      <textarea
        id={id}
        rows={rows}
        value={value}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-2xl border bg-white px-4 py-3 text-base placeholder:text-forest/40 ${
          error ? "border-critical" : "border-forest/20"
        }`}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-2 text-sm text-forest/70">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} role="alert" className="mt-2 text-sm font-bold text-critical">
          {error}
        </p>
      )}
    </div>
  );
}

export function SelectField({
  id,
  label,
  value,
  onChange,
  options,
  error,
  placeholder = "Choose…",
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: readonly { key: string; label: string }[];
  error?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block font-bold">
        {label}
      </label>
      <select
        id={id}
        value={value}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-err` : undefined}
        onChange={(e) => onChange(e.target.value)}
        className={`${inputCls} ${error ? "border-critical" : "border-forest/20"}`}
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}
          </option>
        ))}
      </select>
      {error && (
        <p id={`${id}-err`} role="alert" className="mt-2 text-sm font-bold text-critical">
          {error}
        </p>
      )}
    </div>
  );
}

/** A radio group shown as large tappable cards. */
export function ChoiceGroup({
  name,
  legend,
  options,
  value,
  onChange,
  error,
  columns = "sm:grid-cols-2",
}: {
  name: string;
  legend: string;
  options: readonly { key: string; label: string; hint: string }[];
  value: string;
  onChange: (key: string) => void;
  error?: string;
  columns?: string;
}) {
  return (
    <fieldset aria-describedby={error ? `${name}-err` : undefined}>
      <legend className="mb-3 font-bold">{legend}</legend>
      <div className={`grid gap-3 ${columns}`}>
        {options.map((o) => {
          const on = value === o.key;
          return (
            <label
              key={o.key}
              className={`flex cursor-pointer flex-col gap-2 rounded-2xl border p-4 transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-leaf ${
                on ? "border-forest bg-lime" : "border-forest/20 bg-white hover:border-forest/50"
              }`}
            >
              <input
                type="radio"
                name={name}
                value={o.key}
                checked={on}
                onChange={() => onChange(o.key)}
                className="sr-only"
              />
              <span className="font-bold">{o.label}</span>
              <span className="text-sm text-forest/75">{o.hint}</span>
            </label>
          );
        })}
      </div>
      {error && (
        <p id={`${name}-err`} role="alert" className="mt-2 text-sm font-bold text-critical">
          {error}
        </p>
      )}
    </fieldset>
  );
}

export function FormHeading({ children, sub }: { children: ReactNode; sub?: string }) {
  return (
    <div className="mb-8">
      <h1 className="h-display text-3xl md:text-4xl">{children}</h1>
      {sub && <p className="mt-4 max-w-xl text-forest/80">{sub}</p>}
    </div>
  );
}
