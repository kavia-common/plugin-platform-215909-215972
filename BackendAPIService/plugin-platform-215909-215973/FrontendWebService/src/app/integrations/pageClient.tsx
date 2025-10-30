/* Client-side Integrations page that lists existing connections and basic statuses */
"use client"

import { useEffect, useState } from "react"
import { apiListConnections, type ConnectionListResponse } from "@/lib/api"

export default function IntegrationsPageClient() {
  const [data, setData] = useState<ConnectionListResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await apiListConnections()
        if (mounted) setData(res)
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load connections")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  if (loading) return <div>Loading connections…</div>
  if (error) return <div role="alert">Error: {error}</div>
  const items = data?.items || []
  if (items.length === 0) return <div>No connections yet.</div>

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Connections</h2>
      <ul className="space-y-2">
        {items.map((c) => (
          <li key={c.id} className="border rounded p-3">
            <div className="font-medium">{c.display_name || c.connector}</div>
            <div className="text-sm text-gray-600">
              Connector: {c.connector} • Status: {c.status}
            </div>
            <div className="text-xs text-gray-500">
              ID: {c.id} • Tenant: {c.tenant_id}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
