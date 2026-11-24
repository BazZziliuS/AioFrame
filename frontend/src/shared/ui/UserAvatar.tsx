import { Avatar } from "@heroui/react";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return (parts[0]?.[0] ?? "?").concat(parts[1]?.[0] ?? "").toUpperCase();
}

type Props = {
  name: string;
  photoUrl?: string | null;
  size?: "sm" | "md" | "lg";
};

export function UserAvatar({ name, photoUrl, size = "md" }: Props) {
  return (
    <Avatar size={size} color="accent" variant="soft">
      {photoUrl && <Avatar.Image alt={name} src={photoUrl} />}
      <Avatar.Fallback>{initials(name)}</Avatar.Fallback>
    </Avatar>
  );
}
