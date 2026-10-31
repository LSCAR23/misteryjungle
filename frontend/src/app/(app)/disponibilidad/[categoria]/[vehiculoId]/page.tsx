export default async function Page({
  params,
}: {
  params: Promise<{ categoria: string; vehiculoId: string }>;
}) {
  const p = await params;
  return (
    <div>
      <h1 className="font-display p-4 text-2xl font-bold uppercase tracking-wide">Detalle de vehículo</h1>
      <p className="px-4 text-ink-muted">{Object.values(p).join(" / ")}</p>
    </div>
  );
}
