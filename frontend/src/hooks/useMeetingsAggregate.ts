import { useCallback, useEffect, useState } from "react";
import { fetchMeetingsAggregate, MeetingsAggregate } from "../services/meetings";
import { toErrorMessage } from "../services/api";

interface UseMeetingsAggregateResult {
  data: MeetingsAggregate | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useMeetingsAggregate(): UseMeetingsAggregateResult {
  const [data, setData] = useState<MeetingsAggregate | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const aggregate = await fetchMeetingsAggregate();
      setData(aggregate);
    } catch (err) {
      setError(toErrorMessage(err, "Failed to load your meetings."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshToken]);

  const refresh = useCallback(() => setRefreshToken((n) => n + 1), []);

  return { data, isLoading, error, refresh };
}
