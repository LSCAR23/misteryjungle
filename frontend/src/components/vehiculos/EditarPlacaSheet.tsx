"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button, FieldHint, Input, Label, Select, Sheet } from "@/components/ui";
import { apiFetch, ApiError } from "@/lib/api";
import { UBICACIONES_REALES, type UbicacionReal } from "@/lib/constants";
import type { Placa } from "@/lib/types";

export interface EditarPlacaSheetProps {
  placa: Placa | null;
  onClose: () => void;
  onSaved: () => void;
}

function Form({ placa, onClose, onSaved }: { placa: Placa; onClose: () => void; onSaved: () => void }) {
  const rentada = placa.estado === "Rentada";
  const [texto, setTexto] = useState(placa.placa === "NUEVA" ? "" : placa.placa);
  const [ubi, setUbi] = useState<string>(
    (UBICACIONES_REALES as readonly string[]).includes(placa.ubicacion_actual) ? placa.ubicacion_actual : "",
  );
  const [saving, setSaving] = useState(false);

  async function guardar() {
    const body: { placa: string; ubicacion_actual?: UbicacionReal } = { placa: texto.trim() || "NUEVA" };
    if (!rentada && ubi && ubi !== placa.ubicacion_actual) body.ubicacion_actual = ubi as UbicacionReal;
    setSaving(true);
    try {
      await apiFetch(`/placas/${placa.id}`, { method: "PATCH", body });
      toast.success("Placa actualizada");
      onSaved();
      onClose();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet
      open
      onClose={onClose}
      title="Editar placa"
      footer={
        <Button fullWidth size="lg" loading={saving} onClick={guardar}>
          Guardar
        </Button>
      }
    >
      <div className="space-y-4 py-2">
        <div>
          <Label htmlFor="placa-texto">Placa</Label>
          <Input
            id="placa-texto"
            value={texto}
            maxLength={20}
            autoCapitalize="characters"
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Vacío = NUEVA"
          />
          <FieldHint>Déjala vacía para marcarla como NUEVA.</FieldHint>
        </div>
        <div>
          <Label htmlFor="placa-ubi">Ubicación</Label>
          <Select id="placa-ubi" value={ubi} disabled={rentada} onChange={(e) => setUbi(e.target.value)}>
            {!ubi && <option value="">Ubicación no actualizada</option>}
            {UBICACIONES_REALES.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </Select>
          {rentada && <FieldHint>No se puede cambiar la ubicación de una placa rentada.</FieldHint>}
        </div>
      </div>
    </Sheet>
  );
}

export default function EditarPlacaSheet({ placa, onClose, onSaved }: EditarPlacaSheetProps) {
  if (!placa) return null;
  return <Form key={placa.id} placa={placa} onClose={onClose} onSaved={onSaved} />;
}
