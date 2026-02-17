export interface FingerprintPort {
  getFingerprint(): Promise<string>;
}
