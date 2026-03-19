import { cn, stageColor } from "@/lib/utils";

interface StageBadgeProps {
  stage: string;
}

export function StageBadge({ stage }: StageBadgeProps) {
  return (
    <span className={cn("badge capitalize", stageColor(stage))}>{stage}</span>
  );
}
