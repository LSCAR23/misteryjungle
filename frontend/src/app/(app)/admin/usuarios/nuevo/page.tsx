"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { ApiError, apiFetch } from "@/lib/api";
import type { Rol, Usuario } from "@/lib/types";
import {
  Button,
  Card,
  FieldError,
  FieldHint,
  Input,
  Label,
  PageHeader,
  SegmentedControl,
} from "@/components/ui";

const ROLES: readonly { value: Rol; label: string }[] = [
  { value: "empleado", label: "Empleado" },
  { value: "admin", label: "Admin" },
];

export default function NuevoUsuarioPage() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState<Rol>("empleado");
  const [show, setShow] = useState(false);
  const [errors, setErrors] = useState<{ username?: string; password?: string; form?: string }>({});
  const [saving, setSaving] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const u = username.trim();
    const errs: typeof errors = {};
    if (u.length < 3 || u.length > 50) errs.username = "Debe tener entre 3 y 50 caracteres";
    else if (!/^[A-Za-z0-9._-]+$/.test(u)) errs.username = "Solo letras, números, punto, guion y guion bajo";
    if (password.length < 6) errs.password = "Mínimo 6 caracteres";
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setSaving(true);
    try {
      await apiFetch<Usuario>("/usuarios", { method: "POST", body: { username: u, password, rol } });
      toast.success("Usuario creado");
      await mutate("/usuarios");
      router.push("/admin/usuarios");
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "No se pudo crear el usuario";
      if (err instanceof ApiError && err.status === 409) setErrors({ username: msg });
      else setErrors({ form: msg });
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <PageHeader title="Nuevo usuario" backHref="/admin/usuarios" />
      <form onSubmit={onSubmit} noValidate>
        <Card className="space-y-5 p-4">
          <div>
            <Label htmlFor="username">Usuario</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
              autoCapitalize="none"
              spellCheck={false}
              aria-invalid={!!errors.username}
            />
            {errors.username ? <FieldError>{errors.username}</FieldError> : <FieldHint>Letras, números, punto, guion</FieldHint>}
          </div>
          <div>
            <Label htmlFor="password">Contraseña</Label>
            <div className="relative">
              <Input
                id="password"
                type={show ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                className="pr-12"
                aria-invalid={!!errors.password}
              />
              <button
                type="button"
                onClick={() => setShow((s) => !s)}
                aria-label={show ? "Ocultar contraseña" : "Mostrar contraseña"}
                className="absolute right-1 top-1/2 flex size-11 -translate-y-1/2 items-center justify-center rounded-lg text-ink-muted hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
              >
                {show ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
              </button>
            </div>
            {errors.password ? <FieldError>{errors.password}</FieldError> : <FieldHint>Mínimo 6 caracteres</FieldHint>}
          </div>
          <div>
            <Label>Rol</Label>
            <SegmentedControl options={ROLES} value={rol} onChange={setRol} className="w-full" aria-label="Rol" />
          </div>
          {errors.form && <FieldError>{errors.form}</FieldError>}
          <Button type="submit" size="lg" fullWidth loading={saving}>
            Crear usuario
          </Button>
        </Card>
      </form>
    </div>
  );
}
