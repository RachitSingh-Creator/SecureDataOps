export interface User {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserPayload {
  name: string;
  email: string;
  phone?: string | null;
}
