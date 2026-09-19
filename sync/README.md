# sync/ — service de synchronisation (Cloudflare Worker + D1, gratuit)

Déployé sur le compte Cloudflare de Max. Palier gratuit : 100 000 requêtes/jour, D1 5 M lectures + 100 000 écritures/jour.

    npx wrangler login                         # une fois (navigateur)
    npx wrangler d1 create zazzulist           # une fois -> coller database_id dans wrangler.toml
    npx wrangler d1 execute zazzulist --remote --file schema.sql
    npx wrangler deploy                        # à chaque modification de worker.js

URL publique : voir `SYNC_URL` dans docs/index.html. Test : `curl https://<worker>/v1/health`.
