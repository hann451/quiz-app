#!/bin/bash
set -e

echo "=== Building pawapuro-wiki (Astro) ==="
cd wiki
npm install
npm run build
cd ..

echo "=== Wiki build complete! ==="
echo "You can now run the Flask app:"
echo "python app.py"
# Or if this is deployed to Render/Heroku, they can use this script as the Build Command:
# ./build.sh && pip install -r requirements.txt
