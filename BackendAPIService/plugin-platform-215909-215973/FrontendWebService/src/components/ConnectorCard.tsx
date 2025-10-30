"use client"

import { useState } from "react"
import Link from "next/link"

type Connector = {
  name: string
  title: string
  description: string
  status?: string
  categories?: string[]
  docs_url?: string | null
}

export function ConnectorCard({ connector }: { connector: Connector }) {
  const [busy, setBusy] = useState(false)

  const oauthLoginHref = (name: string) => {
    // For mock flow, the FE would call POST /connectors/{id}/oauth/login and then redirect user to authorize_url.
    // Since static export constraints apply, we can link to backend's mocked authorize_url by first navigating to a local page or instructing the user.
    // Minimal UX: link to backend callback directly with a fake state to create a mock connection is not correct.
    // Instead, present a "Connect (Mock)" button description.
    return "#"
  }

  return (
    <div className="border rounded p-4 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{connector.title}</h3>
        <span className="text-xs uppercase text-gray-500">{connector.status || "beta"}</span>
      </div>
      <p className="text-sm text-gray-700">{connector.description}</p>
      {connector.docs_url && (
        <a className="text-sm text-blue-600 underline" href={connector.docs_url} target="_blank" rel="noreferrer">
          Docs
        </a>
      )}
      <div className="flex gap-2">
        <button
          className="px-3 py-1 rounded bg-black text-white disabled:opacity-50"
          disabled={busy}
          onClick={() => {
            // Instructional note: In local dev, use the Integrations page plus /connectors/:id/oauth/login via a small script or curl.
            alert(
              "To connect (mock), call POST /connectors/{id}/oauth/login then GET /connectors/{id}/oauth/callback using your browser with the returned state."
            )
          }}
        >
          Connect (Mock)
        </button>
        <Link className="px-3 py-1 rounded border" href={`/search?connector=${encodeURIComponent(connector.name)}`}>
          Search
        </Link>
      </div>
    </div>
  )
}
