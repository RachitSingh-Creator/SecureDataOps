import { Save, UserPlus, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import type { User, UserPayload } from "../types";

interface UserFormProps {
  selectedUser: User | null;
  isSubmitting: boolean;
  onSubmit: (payload: UserPayload) => Promise<void>;
  onCancelEdit: () => void;
}

const initialForm = {
  name: "",
  email: "",
  phone: "",
};

export function UserForm({ selectedUser, isSubmitting, onSubmit, onCancelEdit }: UserFormProps) {
  const [form, setForm] = useState(initialForm);
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    if (selectedUser) {
      setForm({
        name: selectedUser.name,
        email: selectedUser.email,
        phone: selectedUser.phone ?? "",
      });
      setValidationError("");
      return;
    }
    setForm(initialForm);
  }, [selectedUser]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError("");

    if (!form.name.trim() || !form.email.trim()) {
      setValidationError("Name and email are required.");
      return;
    }

    await onSubmit({
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
    });

    if (!selectedUser) {
      setForm(initialForm);
    }
  }

  const isEditing = Boolean(selectedUser);

  return (
    <section className="panel user-form-panel" aria-labelledby="user-form-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{isEditing ? "Edit User" : "Create User"}</p>
          <h2 id="user-form-title">{isEditing ? selectedUser?.name : "Add a user"}</h2>
        </div>
      </div>

      <form className="user-form" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            placeholder="Ada Lovelace"
            required
          />
        </label>

        <label>
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            placeholder="ada@example.com"
            required
          />
        </label>

        <label>
          <span>Phone</span>
          <input
            value={form.phone}
            onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))}
            placeholder="+15551234567"
          />
        </label>

        {validationError ? <p className="inline-error">{validationError}</p> : null}

        <div className="form-actions">
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isEditing ? <Save size={18} /> : <UserPlus size={18} />}
            {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Create user"}
          </button>
          {isEditing ? (
            <button className="secondary-button" type="button" onClick={onCancelEdit}>
              <X size={18} />
              Cancel
            </button>
          ) : null}
        </div>
      </form>
    </section>
  );
}
