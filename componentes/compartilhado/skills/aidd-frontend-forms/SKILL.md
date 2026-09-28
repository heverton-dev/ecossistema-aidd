---
name: aidd-frontend-forms
description: 'Use when creating, reviewing, or refactoring typed frontend forms in Next.js using Zod validation schemas and React Hook Form.'
---

# Frontend Forms & Validation (Next.js + Zod)

## Overview

Build robust, type-safe frontend forms in Next.js applications aligning with Ecosystem Law #11 (Next.js + TypeScript + Tailwind CSS). Enforce schema-first validation using Zod and binding with React Hook Form.

## Core Rules

1. **Schema as Single Source of Truth:**
   - Define validation schema in `<feature>-form.schema.ts`.
   - Derive TypeScript form types using `z.infer<typeof FormSchema>`.
   - Never duplicate manual TypeScript interfaces for form data.

2. **File Naming & Structure:**
   - Schema file: `src/modules/<feature>/<feature>-form.schema.ts`
   - Form Component: `src/modules/<feature>/components/<feature>-form.component.tsx`
   - Custom Hook (optional for complex logic): `src/modules/<feature>/hooks/use-<feature>-form.hook.ts`

3. **Validation & UX Invariants:**
   - Always sanitize string inputs (e.g. `.trim()`).
   - Use custom error messages in user language for every constraint.
   - Disable submission button while `isSubmitting` is true to prevent duplicate submissions.
   - Display actionable inline error messages associated with the specific field.

## Implementation Pattern

### 1. Define Schema (`produto-form.schema.ts`)

```typescript
import { z } from 'zod';

export const produtoFormSchema = z.object({
  nome: z.string().trim().min(3, 'Nome deve conter pelo menos 3 caracteres'),
  preco_centavos: z.coerce.number().int().positive('Preço deve ser maior que zero'),
  categoria: z.enum(['HARDWARE', 'SOFTWARE', 'SERVICO'], {
    errorMap: () => ({ message: 'Selecione uma categoria válida' }),
  }),
});

export type ProdutoFormData = z.infer<typeof produtoFormSchema>;
```

### 2. Form Component (`produto-form.component.tsx`)

```tsx
'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { produtoFormSchema, ProdutoFormData } from '../produto-form.schema';

interface ProdutoFormProps {
  onSubmit: (data: ProdutoFormData) => Promise<void>;
  initialData?: Partial<ProdutoFormData>;
}

export function ProdutoFormComponent({ onSubmit, initialData }: ProdutoFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProdutoFormData>({
    resolver: zodResolver(produtoFormSchema),
    defaultValues: initialData,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Nome</label>
        <input
          {...register('nome')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
        {errors.nome && <p className="text-sm text-red-600">{errors.nome.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Preço (centavos)</label>
        <input
          type="number"
          {...register('preco_centavos')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
        {errors.preco_centavos && (
          <p className="text-sm text-red-600">{errors.preco_centavos.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? 'Salvando...' : 'Salvar'}
      </button>
    </form>
  );
}
```
