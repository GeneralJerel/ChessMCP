import { useOpenAiGlobal } from "./use-openai-global";

export function useToolInput<T = unknown>(): T | null {
  return useOpenAiGlobal("toolInput") as T | null;
}

export function useToolOutput<T = unknown>(): T | null {
  return useOpenAiGlobal("toolOutput") as T | null;
}

export function useToolResponseMetadata<T = unknown>(): T | null {
  return useOpenAiGlobal("toolResponseMetadata") as T | null;
}

