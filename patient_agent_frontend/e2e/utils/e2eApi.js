export async function resetE2EState(scenario = 'baseline') {
  const response = await fetch('http://127.0.0.1:8001/api/e2e/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  })
  if (!response.ok) {
    throw new Error(`reset failed: ${response.status}`)
  }
}
