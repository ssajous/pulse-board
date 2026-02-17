/**
 * Compute the expected score delta for an optimistic update.
 *
 * @param currentUserVote - The user's current vote (1, -1, or null)
 * @param direction - The vote direction being cast ("up" or "down")
 * @returns The delta to apply to the score
 */
export function computeScoreDelta(
  currentUserVote: number | null,
  direction: "up" | "down"
): number {
  const newValue = direction === "up" ? 1 : -1;

  if (currentUserVote === null) {
    // New vote
    return newValue;
  }
  if (currentUserVote === newValue) {
    // Cancel (same direction = undo)
    return -currentUserVote;
  }
  // Toggle (different direction = swing by 2)
  return newValue - currentUserVote;
}
