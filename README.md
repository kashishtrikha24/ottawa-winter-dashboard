# Ottawa Winter 2026 — Earth Engine + Streamlit

## Files
- `Ottawa_Winter2026_GEE.ipynb` — run this in Google Colab first.
- `streamlit_app.py` — the web UI.
- `ottawa_winter_2026_rgb.png` — created by the notebook (Step 5); place it next
  to `streamlit_app.py` before deploying.

## 1. Run the notebook
1. Upload `Ottawa_Winter2026_GEE.ipynb` to Google Colab (or open it from Drive).
2. Sign up for a free Earth Engine account at https://code.earthengine.google.com
   if you haven't already, and make sure you have a Google Cloud project with
   the Earth Engine API enabled.
3. Set `EE_PROJECT_ID` in the notebook's Step 1 cell to that project's ID.
4. Run all cells top to bottom. The first Earth Engine call will prompt a
   Google sign-in — follow it.
5. Step 5 downloads `ottawa_winter_2026_rgb.png` into your Colab session.
   Download it from the Colab file browser (folder icon on the left) to your
   computer.

## 2. Set up the Streamlit app
1. Create a GitHub repo containing `streamlit_app.py` and the downloaded
   `ottawa_winter_2026_rgb.png` (same folder).
2. (Optional, for "Live" mode) Create a Google service account with Earth
   Engine access, generate a JSON key, and add its email + key contents to the
   app's Streamlit secrets as `EE_SERVICE_ACCOUNT` and `EE_PRIVATE_KEY`.
3. Add a `requirements.txt` with:
   ```
   streamlit
   earthengine-api
   geemap
   ```

## 3. Deploy to get a shareable link
1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click "New app", pick your repo/branch, and set the main file to
   `streamlit_app.py`.
3. Deploy — Streamlit gives you a public URL like
   `https://your-app-name.streamlit.app`. That's the link to submit.

## Notes
- "Static" mode (default) needs no credentials on the server — it just shows
  the PNG the notebook exported. This is the fastest path to a working link.
- "Live" mode re-queries Earth Engine from the deployed app itself and shows
  an interactive map, but requires the service-account secrets step above.
