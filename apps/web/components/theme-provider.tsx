/**
 * Theme Provider Component
 *
 * Provides theme context and dark mode functionality for the application.
 * Integrates with next-themes for seamless theme switching.
 */

"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
