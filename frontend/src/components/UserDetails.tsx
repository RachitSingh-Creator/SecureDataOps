import { CalendarClock, Mail, Phone, UserRound } from "lucide-react";

import type { User } from "../types";
import { formatDate } from "../utils/format";

interface UserDetailsProps {
  user: User | null;
}

export function UserDetails({ user }: UserDetailsProps) {
  return (
    <section className="panel details-panel" aria-labelledby="details-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">User Details</p>
          <h2 id="details-title">{user ? user.name : "No user selected"}</h2>
        </div>
      </div>

      {user ? (
        <dl className="details-list">
          <div>
            <dt>
              <UserRound size={16} /> ID
            </dt>
            <dd>{user.id}</dd>
          </div>
          <div>
            <dt>
              <Mail size={16} /> Email
            </dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>
              <Phone size={16} /> Phone
            </dt>
            <dd>{user.phone || "Not provided"}</dd>
          </div>
          <div>
            <dt>
              <CalendarClock size={16} /> Created
            </dt>
            <dd>{formatDate(user.created_at)}</dd>
          </div>
          <div>
            <dt>
              <CalendarClock size={16} /> Updated
            </dt>
            <dd>{formatDate(user.updated_at)}</dd>
          </div>
        </dl>
      ) : (
        <p className="muted">Select a user from the table to inspect the complete Phase 1 record.</p>
      )}
    </section>
  );
}
