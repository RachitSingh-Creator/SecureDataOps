import { Database, RefreshCw, ShieldCheck, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { UserDetails } from "./components/UserDetails";
import { UserForm } from "./components/UserForm";
import { UserTable } from "./components/UserTable";
import { userApi } from "./services/api";
import type { User, UserPayload } from "./types";

function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadUsers() {
    setIsLoading(true);
    setError("");
    try {
      const data = await userApi.listUsers();
      setUsers(data);
      setSelectedUser((current) => data.find((user) => user.id === current?.id) ?? data[0] ?? null);
      setEditingUser((current) => (current ? data.find((user) => user.id === current.id) ?? null : null));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load users.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  async function handleSubmit(payload: UserPayload) {
    setIsSubmitting(true);
    setError("");
    setSuccess("");
    try {
      const savedUser = editingUser ? await userApi.updateUser(editingUser.id, payload) : await userApi.createUser(payload);
      setSuccess(editingUser ? "User updated successfully." : "User created successfully.");
      setSelectedUser(savedUser);
      setEditingUser(null);
      await loadUsers();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save user.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(user: User) {
    const confirmed = window.confirm(`Delete ${user.name}? This removes the Phase 1 user record.`);
    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");
    try {
      await userApi.deleteUser(user.id);
      setSuccess("User deleted successfully.");
      if (selectedUser?.id === user.id) {
        setSelectedUser(null);
      }
      if (editingUser?.id === user.id) {
        setEditingUser(null);
      }
      await loadUsers();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to delete user.");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark">
            <ShieldCheck size={24} />
          </span>
          <div>
            <p className="eyebrow">Phase 1</p>
            <h1>SecureDataOps</h1>
          </div>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadUsers()} disabled={isLoading}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </header>

      <section className="stats-band" aria-label="Dashboard summary">
        <article className="stat-card">
          <Users size={22} />
          <div>
            <span>Total Users</span>
            <strong>{users.length}</strong>
          </div>
        </article>
        <article className="stat-card">
          <Database size={22} />
          <div>
            <span>Persistence</span>
            <strong>PostgreSQL</strong>
          </div>
        </article>
      </section>

      {error ? <div className="alert error-alert">{error}</div> : null}
      {success ? <div className="alert success-alert">{success}</div> : null}

      <section className="dashboard-grid">
        <div className="main-column">
          <section className="panel" aria-labelledby="users-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Dashboard</p>
                <h2 id="users-title">Users</h2>
              </div>
              {isLoading ? <span className="status-pill">Loading</span> : <span className="status-pill">{users.length} records</span>}
            </div>
            {isLoading ? <div className="loading-state">Loading users...</div> : (
              <UserTable
                users={users}
                selectedUserId={selectedUser?.id ?? null}
                onSelect={setSelectedUser}
                onEdit={(user) => {
                  setEditingUser(user);
                  setSelectedUser(user);
                }}
                onDelete={(user) => void handleDelete(user)}
              />
            )}
          </section>
        </div>

        <aside className="side-column">
          <UserForm selectedUser={editingUser} isSubmitting={isSubmitting} onSubmit={handleSubmit} onCancelEdit={() => setEditingUser(null)} />
          <UserDetails user={selectedUser} />
        </aside>
      </section>
    </main>
  );
}

export default App;
