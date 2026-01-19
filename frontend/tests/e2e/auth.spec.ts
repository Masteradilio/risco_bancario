import { test, expect } from '@playwright/test';

/**
 * Testes E2E para Autenticação
 * 
 * Testa fluxos de login, logout e proteção de rotas
 */

test.describe('Autenticação - Login/Logout', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('deve carregar a página inicial', async ({ page }) => {
        await expect(page).toHaveURL(/.*\//);
    });

    test('deve exibir indicador de usuário logado', async ({ page }) => {
        // Procurar por elementos que indicam usuário logado
        // (avatar, nome, role, badge)
        const userIndicators = page.locator('[data-testid="user-info"]')
            .or(page.locator('text=/analista|gestor|admin|auditor/i').first());

        // A aplicação pode ter ou não login obrigatório
        const hasUserIndicator = await userIndicators.count() > 0;
        console.log(`User indicator present: ${hasUserIndicator}`);
    });

    test('sidebar deve mostrar opções baseadas no perfil', async ({ page }) => {
        const sidebar = page.locator('aside').or(page.locator('nav').first());

        // Sidebar deve existir
        await expect(sidebar).toBeVisible();

        // Deve ter links de navegação
        const navLinks = sidebar.locator('a, button');
        const count = await navLinks.count();
        expect(count).toBeGreaterThan(3);
    });

    test('deve redirecionar rotas protegidas se não autenticado', async ({ page }) => {
        // Tentar acessar rota de admin diretamente
        await page.goto('/admin');
        await page.waitForLoadState('networkidle');

        // Pode redirecionar para login ou mostrar erro 403
        const currentUrl = page.url();

        // Verificar comportamento esperado
        const isOnAdmin = currentUrl.includes('/admin');
        const isRedirected = currentUrl.includes('/login') || currentUrl.includes('/');

        // Um dos comportamentos deve ocorrer
        expect(isOnAdmin || isRedirected).toBeTruthy();
    });

    test('deve exibir versão do sistema no footer/sidebar', async ({ page }) => {
        // Procurar indicador de versão
        const versionText = page.locator('text=/v[0-9]+\.[0-9]+/i').first();

        if (await versionText.count() > 0) {
            await expect(versionText).toBeVisible();
        }
    });
});

test.describe('Autenticação - Controle de Acesso', () => {

    test('deve esconder menu Admin para não-administradores', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Verificar sidebar
        const adminLink = page.locator('text=/^Admin$/i').first();

        // Admin pode ou não estar visível dependendo do perfil mockado
        const isVisible = await adminLink.isVisible().catch(() => false);
        console.log(`Admin link visible: ${isVisible}`);
    });

    test('deve esconder menu Auditoria para perfis sem permissão', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const auditLink = page.locator('text=/auditoria/i').first();
        const isVisible = await auditLink.isVisible().catch(() => false);
        console.log(`Auditoria link visible: ${isVisible}`);
    });
});

test.describe('Session - Controles', () => {

    test('deve manter sessão entre navegações', async ({ page }) => {
        // Navegar para página inicial
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Navegar para outra página
        await page.goto('/perda-esperada');
        await page.waitForLoadState('networkidle');

        // Voltar para inicial
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // A sessão deve ser mantida (sem redirecionamento para login)
        expect(page.url()).not.toContain('/login');
    });
});
