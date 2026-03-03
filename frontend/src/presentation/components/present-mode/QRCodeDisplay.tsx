import { QRCodeSVG } from "qrcode.react";

interface QRCodeDisplayProps {
  url: string;
  size?: number;
}

export const QRCodeDisplay = ({
  url,
  size = 200,
}: QRCodeDisplayProps) => {
  return (
    <div
      id="present-qr-code"
      data-join-url={url}
      className="rounded bg-white p-2"
    >
      <QRCodeSVG value={url} size={size} />
    </div>
  );
};
