import { Card, Skeleton } from "@heroui/react";

export function ProfileSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-busy="true">
      <Skeleton className="h-8 w-32 rounded-lg" />
      <Card>
        <Card.Header className="flex-row items-center gap-3">
          <Skeleton className="size-12 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-2/5 rounded-md" />
            <Skeleton className="h-3 w-1/4 rounded-md" />
          </div>
        </Card.Header>
        <Card.Content className="gap-4 py-2">
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-full rounded-md" />
        </Card.Content>
      </Card>
    </div>
  );
}
