import { PageHeader } from "@/components/ui";
import VehiculoForm from "@/components/admin/VehiculoForm";

export default function NuevoVehiculoPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Nuevo vehículo" backHref="/admin/vehiculos" />
      <VehiculoForm />
    </div>
  );
}
