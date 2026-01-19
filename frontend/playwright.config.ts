import { defineConfig, devices } from '@playwright/test';

/**
 * Configuração do Playwright para testes E2E
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
    testDir: './tests/e2e',

    /* Timeout máximo por teste */
    timeout: 30 * 1000,

    /* Timeout para expect */
    expect: {
        timeout: 5000
    },

    /* Rodar testes em paralelo */
    fullyParallel: true,

    /* Falhar o build em CI se houver test.only */
    forbidOnly: !!process.env.CI,

    /* Número de retries */
    retries: process.env.CI ? 2 : 0,

    /* Número de workers */
    workers: process.env.CI ? 1 : undefined,

    /* Reporter */
    reporter: 'html',

    /* Configurações compartilhadas para todos os testes */
    use: {
        /* URL base da aplicação */
        baseURL: 'http://localhost:5173',

        /* Tirar screenshot em caso de falha */
        screenshot: 'only-on-failure',

        /* Video */
        video: 'retain-on-failure',

        /* Trace */
        trace: 'on-first-retry',
    },

    /* Projetos de teste por navegador */
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },
    ],

    /* Iniciar servidor de dev antes dos testes */
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
    },
});
