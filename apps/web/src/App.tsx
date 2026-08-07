import { useState } from 'react';
import './App.css';

/**
 * Ω∞v Oceanicos Web Dashboard
 * Visualizes the verification loop in real-time
 */
export function App(): JSX.Element {
  const [observation, setObservation] = useState<string>('');
  const [claim, setClaim] = useState<string>('Service X is healthy');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const executeVerificationLoop = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/complete-loop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          claim,
          category: 'health-check',
          source: {
            system: 'web-dashboard',
            version: '0.1.0',
            environment: 'production',
          },
          observedBy: 'user',
          metadata: {
            responseTime: Math.random() * 200,
            statusCode: 200,
          },
          confidence: 0.95,
          confidenceReason: 'Manual verification from dashboard',
        }),
      });

      const data = (await response.json()) as { data: object };
      setResults(data.data);
      setObservation('Verification complete');
    } catch (error) {
      setObservation(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Ω∞v Oceanicos</h1>
        <p>Verification-First Full-Stack Ecosystem</p>
      </header>

      <main className="main">
        <section className="input-section">
          <h2>Execute Verification Loop</h2>
          <div className="form-group">
            <label htmlFor="claim">Claim:</label>
            <input
              id="claim"
              type="text"
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              placeholder="Enter a claim to verify"
            />
          </div>
          <button onClick={executeVerificationLoop} disabled={loading} className="btn-primary">
            {loading ? 'Verifying...' : 'Run Verification'}
          </button>
        </section>

        {results && (
          <section className="results-section">
            <h2>Verification Results</h2>

            <div className="step observation">
              <h3>✓ Observation</h3>
              <div className="details">
                <p>
                  <strong>ID:</strong> {results.observation.id}
                </p>
                <p>
                  <strong>Claim:</strong> {results.observation.claim.statement}
                </p>
                <p>
                  <strong>Confidence:</strong> {(results.observation.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            <div className="step verification">
              <h3>✓ Verification</h3>
              <div className="details">
                <p>
                  <strong>Status:</strong>{' '}
                  {results.verification.summary.passed ? '✓ PASSED' : '✗ FAILED'}
                </p>
                <p>
                  <strong>Rules Applied:</strong> {results.verification.summary.rulesApplied}
                </p>
                <p>
                  <strong>Rules Passed:</strong> {results.verification.summary.rulesPassed}
                </p>
                <div className="evidence">
                  <h4>Evidence Path:</h4>
                  <ul>
                    {results.verification.evidencePath.map((step: any, idx: number) => (
                      <li key={idx}>
                        {step.passed ? '✓' : '✗'} {step.rule}: {step.reasoning}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="step attestation">
              <h3>✓ Attestation</h3>
              <div className="details">
                <p>
                  <strong>ID:</strong> {results.attestation.id}
                </p>
                <p>
                  <strong>Verified:</strong> {results.attestation.verified ? '✓ Yes' : '✗ No'}
                </p>
                <p>
                  <strong>Signed At:</strong>{' '}
                  {new Date(results.attestation.attestedAt).toLocaleString()}
                </p>
                <p>
                  <strong>Signature:</strong>{' '}
                  <code>{results.attestation.signature.substring(0, 32)}...</code>
                </p>
              </div>
            </div>
          </section>
        )}

        {observation && (
          <section className="status-section">
            <p className="status">{observation}</p>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Attest, don't assert. Evidence before trust. Verification before evolution.</p>
      </footer>
    </div>
  );
}

export default App;
