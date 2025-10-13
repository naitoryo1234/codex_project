const { webkit } = require('playwright');

(async () => {
  // Safari 相当のブラウザ起動
  const browser = await webkit.launch({ headless: false }); 
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 }, // iPhone 12 Pro サイズ
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
  });

  const page = await context.newPage();
  await page.goto('https://codexproject-v4hjenvtkinm2yk8umqxyz.streamlit.app/#f9e1b8da'); // ← あなたの Streamlit アプリURLに置き換え

  // コンソールエラーをキャッチして表示
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('⚠️ コンソールエラー:', msg.text());
    }
  });

  console.log("✅ WebKit 環境で起動しました。エラーが出ないか確認してください。");
})();
