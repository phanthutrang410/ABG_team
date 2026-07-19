type AIThinkingOverlayProps = {
  visible?: boolean;
};

/**
 * Full-screen pending state used while a route or live API request is loading.
 * The current screen remains visible underneath so navigation does not flash an
 * empty/error-looking page while the next response is still in flight.
 */
export function AIThinkingOverlay({ visible = true }: AIThinkingOverlayProps) {
  if (!visible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="AI Thinking ..."
      className="fixed inset-0 z-[1000] flex cursor-wait items-center justify-center bg-white/75 backdrop-blur-[3px]"
    >
      <p className="text-2xl font-extrabold tracking-[0.08em] text-red-600 drop-shadow-sm md:text-3xl">
        AI Thinking ...
      </p>
    </div>
  );
}
