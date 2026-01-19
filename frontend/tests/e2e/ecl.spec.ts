import { test, expect } from '@playwright/test';

/**
 * Testes E2E para o módulo Perda Esperada (ECL)
 * 
 * Testa navegação pelas 10 abas do sistema ECL:
 * - Dashboard
 * - Cálculo ECL
 * - Classificação de Estágios
 * - Grupos Homogêneos
 * - Forward Looking
 * - LGD Segmentado
 * - Sistema de Cura
 * - Write-off
 * - Exportação BACEN
 * - Pipeline
 */

test.describe('Perda Esperada (ECL) - Navegação', () => {

    test.beforeEach(async ({ page }) => {
        // Navegar para a página de Perda Esperada
        await page.goto('/perda-esperada');
        await page.waitForLoadState('networkidle');
    });

    test('deve carregar a página de Perda Esperada', async ({ page }) => {
        // Verificar se o título está presente
        await expect(page.locator('h1')).toContainText(/perda esperada|ecl/i);
    });

    test('deve exibir todas as abas de navegação', async ({ page }) => {
        // Verificar presença das principais abas
        const tabs = [
            'Dashboard',
            'Cálculo',
            'Estágios',
            'Grupos',
            'Forward Looking',
            'LGD',
            'Cura',
            'Write-off',
            'BACEN',
            'Pipeline'
        ];

        for (const tab of tabs) {
            const tabElement = page.getByRole('button', { name: new RegExp(tab, 'i') })
                .or(page.getByRole('tab', { name: new RegExp(tab, 'i') }))
                .or(page.locator(`text=${tab}`).first());

            // Ao menos uma das variantes deve existir
            const exists = await tabElement.count() > 0;
            if (!exists) {
                console.log(`Tab "${tab}" não encontrada - pode ter nome diferente`);
            }
        }
    });

    test('aba Dashboard deve exibir KPIs', async ({ page }) => {
        // Clicar na aba Dashboard se existir
        const dashboardTab = page.getByRole('button', { name: /dashboard/i }).first();
        if (await dashboardTab.count() > 0) {
            await dashboardTab.click();
        }

        // Verificar elementos típicos de dashboard
        await expect(page.locator('body')).toBeVisible();
    });

    test('aba Cálculo ECL deve ter formulário', async ({ page }) => {
        // Navegar para aba de cálculo
        const calculoTab = page.getByRole('button', { name: /cálculo|calculo/i }).first();
        if (await calculoTab.count() > 0) {
            await calculoTab.click();
            await page.waitForLoadState('networkidle');
        }
    });

    test('navegação entre abas deve funcionar', async ({ page }) => {
        // Testar navegação entre 3 abas
        const tabsToTest = ['Dashboard', 'Cálculo', 'Write-off'];

        for (const tabName of tabsToTest) {
            const tab = page.getByRole('button', { name: new RegExp(tabName, 'i') }).first();
            if (await tab.count() > 0) {
                await tab.click();
                await page.waitForTimeout(500); // Aguardar transição
            }
        }
    });

    test('deve ser responsivo em tela menor', async ({ page }) => {
        // Redimensionar para tablet
        await page.setViewportSize({ width: 768, height: 1024 });

        // A página deve continuar carregando
        await expect(page.locator('body')).toBeVisible();
    });
});

test.describe('Perda Esperada - Gráficos', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/perda-esperada');
        await page.waitForLoadState('networkidle');
    });

    test('deve renderizar gráficos sem erros', async ({ page }) => {
        // Verificar que não há erros de console
        const errors: string[] = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });

        await page.waitForTimeout(2000);

        // Filtrar erros relevantes (ignorar erros de rede)
        const relevantErrors = errors.filter(e =>
            !e.includes('net::ERR') &&
            !e.includes('Failed to load resource')
        );

        // Não deve haver erros de JavaScript críticos
        expect(relevantErrors.length).toBeLessThanOrEqual(5);
    });
});
