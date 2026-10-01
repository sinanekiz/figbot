import { fileURLToPath } from 'node:url';

export default {
  build: {
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        kol: fileURLToPath(new URL('./kol.html', import.meta.url)),
      },
    },
  },
};
