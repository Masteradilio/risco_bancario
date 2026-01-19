---
name: backend_expert
description: Use quando o usuário solicitar criação, manutenção, correção, do backend do projeto do usuário
---

---
name: Backend Expert
description: Skill para desenvolvimento backend robusto, seguro e escalável para aplicações SaaS
trigger: Ative quando trabalhar em APIs, banco de dados, autenticação, integrações, ou qualquer lógica de servidor
---

# Backend Expert Skill

## 🎯 Missão Principal
Desenvolver backends robustos, seguros e escaláveis para aplicações SaaS, seguindo as melhores práticas da indústria e padrões que facilitam manutenção por um solo developer.

## 🏗️ ARQUITETURA E ESTRUTURA

### Estrutura de Projeto Recomendada
src/ ├── app/ # Rotas da aplicação (Next.js App Router) │ └── api/ # API Routes │ └── v1/ # Versionamento de API ├── lib/ # Código compartilhado │ ├── db/ # Configuração e queries do banco │ ├── auth/ # Lógica de autenticação │ ├── email/ # Serviço de email │ ├── payments/ # Integração de pagamentos │ └── utils/ # Utilitários gerais ├── services/ # Lógica de negócio ├── repositories/ # Acesso a dados ├── types/ # TypeScript types/interfaces ├── validations/ # Schemas de validação (Zod) └── config/ # Configurações e constantes




### Princípios de Arquitetura
SEPARAÇÃO DE RESPONSABILIDADES
Routes: Apenas recebem request e retornam response
Services: Contêm lógica de negócio
Repositories: Acesso a dados
Utils: Funções puras e reutilizáveis
DEPENDENCY INJECTION

Facilita testes
Permite trocar implementações
Evita acoplamento forte
FAIL FAST

Valide inputs no início
Retorne erros claros imediatamente
Não deixe erros silenciosos



## 🔐 AUTENTICAÇÃO E AUTORIZAÇÃO

### Padrões de Autenticação para SaaS
```typescript
// Estrutura de sessão recomendada
interface Session {
  user: {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'member' | 'viewer';
    organizationId: string;
  };
  accessToken: string;
  expiresAt: Date;
}

// Middleware de autenticação
export async function withAuth(
  handler: AuthenticatedHandler
): Promise<Response> {
  const session = await getSession();
  
  if (!session) {
    return Response.json(
      { error: 'Unauthorized', code: 'AUTH_REQUIRED' },
      { status: 401 }
    );
  }
  
  return handler(session);
}

// Middleware de autorização por role
export function withRole(allowedRoles: Role[]) {
  return async (handler: AuthenticatedHandler) => {
    const session = await getSession();
    
    if (!session || !allowedRoles.includes(session.user.role)) {
      return Response.json(
        { error: 'Forbidden', code: 'INSUFFICIENT_PERMISSIONS' },
        { status: 403 }
      );
    }
    
    return handler(session);
  };
}
Checklist de Segurança
 Senhas hasheadas com bcrypt/argon2 (cost factor adequado)
 Tokens JWT com expiração curta + refresh tokens
 Rate limiting em endpoints sensíveis
 CSRF protection em forms
 Sanitização de inputs
 Headers de segurança (CORS, CSP, etc.)
 Audit logs para ações sensíveis
📊 BANCO DE DADOS
Design de Schema para SaaS Multi-tenant
sql


-- Padrão: Tenant por coluna (simples e eficiente)
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  plan VARCHAR(50) DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sempre inclua organization_id em tabelas tenant-specific
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  -- ... outros campos
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index para queries frequentes
CREATE INDEX idx_projects_org ON projects(organization_id);
CREATE INDEX idx_users_org ON users(organization_id);
Boas Práticas de Queries
typescript


// ✅ BOM: Query parametrizada
const user = await db
  .select()
  .from(users)
  .where(eq(users.id, userId))
  .limit(1);

// ❌ RUIM: Concatenação de strings (SQL Injection)
const user = await db.query(`SELECT * FROM users WHERE id = '${userId}'`);

// ✅ BOM: Sempre filtre por organization_id
const projects = await db
  .select()
  .from(projects)
  .where(
    and(
      eq(projects.organizationId, session.user.organizationId),
      eq(projects.status, 'active')
    )
  );

// ✅ BOM: Paginação eficiente
const PAGE_SIZE = 20;
const items = await db
  .select()
  .from(items)
  .where(eq(items.organizationId, orgId))
  .orderBy(desc(items.createdAt))
  .limit(PAGE_SIZE)
  .offset((page - 1) * PAGE_SIZE);
Migrations


Regras:
1. NUNCA edite migrations já executadas em produção
2. Migrations devem ser reversíveis quando possível
3. Nomeie descritivamente: 001_create_users_table.sql
4. Teste migrations em ambiente de staging primeiro
5. Faça backup antes de migrations destrutivas
🌐 API DESIGN
Padrões REST
typescript


// Estrutura de response padronizada
interface ApiResponse<T> {
  data?: T;
  error?: {
    message: string;
    code: string;
    details?: Record<string, string[]>;
  };
  meta?: {
    page?: number;
    pageSize?: number;
    total?: number;
    hasMore?: boolean;
  };
}

// HTTP Status Codes corretos
200 - OK (GET bem-sucedido, PUT/PATCH bem-sucedido)
201 - Created (POST bem-sucedido)
204 - No Content (DELETE bem-sucedido)
400 - Bad Request (Validação falhou)
401 - Unauthorized (Não autenticado)
403 - Forbidden (Autenticado, mas sem permissão)
404 - Not Found (Recurso não existe)
409 - Conflict (Duplicata, conflito de estado)
422 - Unprocessable Entity (Validação de negócio falhou)
429 - Too Many Requests (Rate limit)
500 - Internal Server Error (Erro não tratado)
Validação com Zod
typescript


import { z } from 'zod';

// Schema de criação
export const createProjectSchema = z.object({
  name: z.string().min(1, 'Nome é obrigatório').max(255),
  description: z.string().max(1000).optional(),
  isPublic: z.boolean().default(false),
});

// Schema de atualização (tudo opcional)
export const updateProjectSchema = createProjectSchema.partial();

// Uso no handler
export async function POST(request: Request) {
  const body = await request.json();
  
  const result = createProjectSchema.safeParse(body);
  
  if (!result.success) {
    return Response.json({
      error: {
        message: 'Validation failed',
        code: 'VALIDATION_ERROR',
        details: result.error.flatten().fieldErrors,
      }
    }, { status: 400 });
  }
  
  // result.data está tipado e validado
  const project = await projectService.create(result.data);
  
  return Response.json({ data: project }, { status: 201 });
}
Rate Limiting
typescript


import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
  analytics: true,
});

export async function withRateLimit(
  request: Request,
  handler: () => Promise<Response>
): Promise<Response> {
  const ip = request.headers.get('x-forwarded-for') ?? 'anonymous';
  const { success, limit, remaining, reset } = await ratelimit.limit(ip);
  
  if (!success) {
    return Response.json(
      { error: { message: 'Too many requests', code: 'RATE_LIMITED' } },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': limit.toString(),
          'X-RateLimit-Remaining': remaining.toString(),
          'X-RateLimit-Reset': reset.toString(),
        },
      }
    );
  }
  
  return handler();
}
💳 INTEGRAÇÃO DE PAGAMENTOS (Stripe)
Estrutura Recomendada
typescript


// lib/payments/stripe.ts
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

// Criar checkout session
export async function createCheckoutSession({
  organizationId,
  priceId,
  successUrl,
  cancelUrl,
}: CreateCheckoutParams) {
  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: successUrl,
    cancel_url: cancelUrl,
    metadata: { organizationId },
    subscription_data: {
      metadata: { organizationId },
    },
  });
  
  return session;
}

// Webhook handler
export async function handleStripeWebhook(
  body: string,
  signature: string
) {
  const event = stripe.webhooks.constructEvent(
    body,
    signature,
    process.env.STRIPE_WEBHOOK_SECRET!
  );
  
  switch (event.type) {
    case 'checkout.session.completed':
      await handleCheckoutCompleted(event.data.object);
      break;
    case 'customer.subscription.updated':
      await handleSubscriptionUpdated(event.data.object);
      break;
    case 'customer.subscription.deleted':
      await handleSubscriptionDeleted(event.data.object);
      break;
    case 'invoice.payment_failed':
      await handlePaymentFailed(event.data.object);
      break;
  }
}
📧 EMAILS TRANSACIONAIS
Estrutura de Email Service
typescript


// lib/email/index.ts
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

interface SendEmailParams {
  to: string;
  subject: string;
  template: string;
  data: Record<string, unknown>;
}

export async function sendEmail({ to, subject, template, data }: SendEmailParams) {
  const html = await renderTemplate(template, data);
  
  await resend.emails.send({
    from: 'Seu App <noreply@seuapp.com>',
    to,
    subject,
    html,
  });
}

// Emails específicos
export const emails = {
  welcome: (to: string, name: string) =>
    sendEmail({
      to,
      subject: 'Bem-vindo ao App!',
      template: 'welcome',
      data: { name },
    }),
    
  passwordReset: (to: string, resetLink: string) =>
    sendEmail({
      to,
      subject: 'Redefinição de senha',
      template: 'password-reset',
      data: { resetLink },
    }),
    
  invoicePaid: (to: string, invoiceData: InvoiceData) =>
    sendEmail({
      to,
      subject: `Fatura #${invoiceData.number} paga`,
      template: 'invoice-paid',
      data: invoiceData,
    }),
};
🔄 BACKGROUND JOBS
Para Tarefas Assíncronas
typescript


// Usando Inngest, Trigger.dev, ou similar
import { inngest } from '@/lib/inngest';

// Definir o job
export const syncUserData = inngest.createFunction(
  { id: 'sync-user-data' },
  { event: 'user/sync.requested' },
  async ({ event, step }) => {
    const { userId } = event.data;
    
    // Step 1: Buscar dados
    const userData = await step.run('fetch-user', async () => {
      return await userService.getFullProfile(userId);
    });
    
    // Step 2: Sincronizar com serviço externo
    await step.run('sync-external', async () => {
      return await externalService.sync(userData);
    });
    
    // Step 3: Atualizar status
    await step.run('update-status', async () => {
      return await userService.updateSyncStatus(userId, 'completed');
    });
  }
);

// Disparar o job
await inngest.send({
  name: 'user/sync.requested',
  data: { userId: '123' },
});
📝 LOGGING E MONITORAMENTO
Estrutura de Logs
typescript


// lib/logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
});

// Uso contextualizado
export function createLogger(context: string) {
  return logger.child({ context });
}

// Em um service
const log = createLogger('PaymentService');

export async function processPayment(paymentId: string) {
  log.info({ paymentId }, 'Processing payment');
  
  try {
    const result = await stripe.paymentIntents.confirm(paymentId);
    log.info({ paymentId, status: result.status }, 'Payment processed');
    return result;
  } catch (error) {
    log.error({ paymentId, error }, 'Payment failed');
    throw error;
  }
}
✅ CHECKLIST DE QUALIDADE
Antes de Cada Implementação:
 Endpoint precisa de autenticação?
 Precisa verificar permissões (roles)?
 Inputs estão sendo validados?
 Queries filtram por organization_id?
 Erros estão sendo tratados adequadamente?
 Logs estão sendo gerados para debugging?
Antes de Deploy:
 Variáveis de ambiente configuradas
 Migrations executadas
 Rate limiting ativo em endpoints públicos
 Webhooks configurados (Stripe, etc.)
 Health check endpoint funcionando
 Backup de banco configurado
🛠️ STACK BACKEND RECOMENDADA


Runtime: Node.js 20+ / Bun
Framework: Next.js API Routes ou Hono
ORM: Drizzle ORM (type-safe, performático)
Database: PostgreSQL (Neon, Supabase, ou Railway)
Cache: Redis (Upstash para serverless)
Auth: Better-Auth, Clerk, ou Auth.js
Validação: Zod
Pagamentos: Stripe
Email: Resend
Jobs: Inngest ou Trigger.dev
Logs: Pino + serviço de agregação
Monitoramento: Sentry para errors



---

## 📚 4. CONTEXT > DOCS (Documentação de Referência)

Na seção **Context > Docs**, adicione URLs de documentação que você usa frequentemente. Isso ajuda o agente a buscar informações atualizadas:

### Documentações Recomendadas para Adicionar:

Essenciais (adicione via URL):

https://nextjs.org/docs
https://tailwindcss.com/docs
https://ui.shadcn.com/docs
https://orm.drizzle.team/docs/overview
https://zod.dev/
https://stripe.com/docs/api
Opcionais (dependendo da sua stack):

https://react.dev/reference/react
https://tanstack.com/query/latest/docs
https://authjs.dev/getting-started
https://resend.com/docs
https://www.inngest.com/docs