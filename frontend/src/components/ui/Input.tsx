import { InputHTMLAttributes, useId, useState } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

/** A labeled text input. Handles its own id/label association. */
export function Field({ label, hint, id, ...rest }: FieldProps) {
  const generatedId = useId();
  const inputId = id || generatedId;

  return (
    <div className="field">
      <label className="field-label" htmlFor={inputId}>
        {label}
      </label>
      <input id={inputId} className="input" {...rest} />
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  );
}

/** A labeled password input with a show/hide toggle. */
export function PasswordField({ label, hint, id, ...rest }: FieldProps) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const [visible, setVisible] = useState(false);

  return (
    <div className="field">
      <label className="field-label" htmlFor={inputId}>
        {label}
      </label>
      <div className="input-wrap">
        <input id={inputId} className="input" type={visible ? "text" : "password"} {...rest} />
        <button
          type="button"
          className="input-adornment-btn"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  );
}
