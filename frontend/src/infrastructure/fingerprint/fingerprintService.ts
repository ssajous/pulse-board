import type { FingerprintPort } from "@domain/ports/FingerprintPort";
import FingerprintJS from "@fingerprintjs/fingerprintjs";

export class FingerprintService implements FingerprintPort {
  private cachedId: string | null = null;

  async getFingerprint(): Promise<string> {
    if (this.cachedId) return this.cachedId;
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    this.cachedId = result.visitorId;
    return this.cachedId;
  }
}
