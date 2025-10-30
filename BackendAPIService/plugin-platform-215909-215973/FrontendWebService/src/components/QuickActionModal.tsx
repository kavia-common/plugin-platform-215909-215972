"use client"

import { useState } from "react"
import { apiCreateIssue, apiCreatePage } from "@/lib/api"

type Props = {
  open: boolean
  onClose: () => void
}

export default function QuickActionModal({ open, onClose }: Props) {
  const [action, setAction] = useState<"issue" | "page">("issue")
  const [title, setTitle] = useState("")
  const [projectKey, setProjectKey] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any | null>(null)

  if (!open) return null

  async function submit() {
    setSubmitting(true)
    setError(null)
    setResult(null)
    try {
      if (!title) throw new Error("Title is required")
      if (action === "issue") {
        const res = await apiCreateIssue("jira", { title, project_key: projectKey || "PP" })
        setResult(res)
      } else {
        const res = await apiCreatePage("confluence", { title, project_key: projectKey || "SPACE" })
        setResult(res)
      }
    } catch (e: any) {
      setError(e?.message || "Action failed")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white rounded p-4 w-full max-w-md space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Quick Action</h3>
          <button onClick={onClose} className="text-sm text-gray-500 hover:text-black">
            Close
          </button>
        </div>
        <div className="space-y-2">
          <label className="block text-sm">
            Action
            <select
              className="block w-full border rounded px-2 py-1 mt-1"
              value={action}
              onChange={(e) => setAction(e.target.value as "issue" | "page")}
            >
              <option value="issue">Create Issue (Jira)</option>
              <option value="page">Create Page (Confluence)</option>
            </select>
          </label>
          <label className="block text-sm">
            Title
            <input
              className="block w-full border rounded px-2 py-1 mt-1"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Short title"
            />
          </label>
          <label className="block text-sm">
            Project/Space Key
            <input
              className="block w-full border rounded px-2 py-1 mt-1"
              value={projectKey}
              onChange={(e) => setProjectKey(e.target.value)}
              placeholder={action === "issue" ? "PP" : "SPACE"}
            />
          </label>
        </div>
        {error && (
          <div role="alert" className="text-sm text-red-600">
            {error}
          </div>
        )}
        {result && (
          <div className="text-sm text-green-700">
            Created {result.type}: <a className="underline" href={result.url} target="_blank" rel="noreferrer">
              {result.title}
            </a>
          </div>
        )}
        <div className="flex justify-end gap-2">
          <button className="px-3 py-1 rounded border" onClick={onClose}>
            Cancel
          </button>
          <button className="px-3 py-1 rounded bg-black text-white disabled:opacity-50" disabled={submitting} onClick={submit}>
            {submitting ? "Submitting…" : "Submit"}
          </button>
        </div>
      </div>
    </div>
  )
}
