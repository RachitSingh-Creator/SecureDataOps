import { Edit3, Trash2 } from "lucide-react";

import type { User } from "../types";
import { formatDate } from "../utils/format";

interface UserTableProps {
  users: User[];
  selectedUserId: string | null;
  onSelect: (user: User) => void;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}

export function UserTable({ users, selectedUserId, onSelect, onEdit, onDelete }: UserTableProps) {
  if (users.length === 0) {
    return (
      <div className="empty-state">
        <h3>No users yet</h3>
        <p>Create the first user to verify the SecureDataOps Phase 1 API flow.</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} className={selectedUserId === user.id ? "selected-row" : ""}>
              <td>
                <button className="link-button" type="button" onClick={() => onSelect(user)}>
                  {user.name}
                </button>
              </td>
              <td>{user.email}</td>
              <td>{user.phone || "Not provided"}</td>
              <td>{formatDate(user.created_at)}</td>
              <td>
                <div className="row-actions">
                  <button className="icon-button" type="button" onClick={() => onEdit(user)} aria-label={`Edit ${user.name}`}>
                    <Edit3 size={17} />
                  </button>
                  <button className="icon-button danger" type="button" onClick={() => onDelete(user)} aria-label={`Delete ${user.name}`}>
                    <Trash2 size={17} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
