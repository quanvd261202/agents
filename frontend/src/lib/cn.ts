import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

/**
 * tailwind-merge must know the custom type scale: without this it reads `text-body` as a colour
 * and drops a real colour such as `text-primary-fg`, leaving a button label unreadable.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [{ text: ["display", "h1", "h2", "h3", "h4", "lead", "body", "small", "caption"] }],
      shadow: [{ shadow: ["sm", "md", "lg", "xl"] }],
      rounded: [{ rounded: ["sm", "card", "lg", "media", "button", "pill"] }],
    },
  },
});

/** Compose class names; later Tailwind utilities win over earlier conflicting ones. */
export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
