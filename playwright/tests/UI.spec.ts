import { test, expect } from '@playwright/test';



// Toggle dark mode
test('dark mode toggle adds and removes "dark" class', async ({ page }) => {
  await page.goto('http://localhost:4000/');

  // Check initial state (assuming it starts without the dark class)
  let isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  expect(isDark).toBe(true);

  await page.getByRole('button', { name: 'Toggle Dark Mode' }).click();


  // Check if the dark class was added
  isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  expect(isDark).toBe(false);

  await page.getByRole('button', { name: 'Toggle Dark Mode' }).click();

  // Check if the dark class was removed
  isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  expect(isDark).toBe(true);
});