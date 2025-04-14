<h1>tc_guidl</h1>
<p>Bulk download Twitch clips from a specific channel and time frame written in Python.</p>

<h2>Prerequisites</h2>
<ul>
  <li>A <strong>Twitch account</strong></li>
  <li>Access to the Twitch Developer Dashboard (only possible with two-factor authentication!)</li>
  <li>Twitch Client-ID and Secret (see below)</li>
  <li>The app <code>tc_guidl.exe</code> - place it in a directory of your choice. Configuration information will be stored in the same directory (<code>config.json</code>).</li>
</ul>

<h2>Configure the app</h2>
<h3>Twitch Authentication</h3>
<ul>
  <li>When the app is run for the first time or no configuration file is found, it automatically shows the Settings page. If you want to make changes later, change to the Settings page by clicking the gear icon.</li>
  <li>Enter Twitch Client-ID and Twitch Client-Secret -> <a href="#twitch">see instructions below</a> how to obtain this</li>
  <li>Click "Create/Renew Auth-Token</li>
</ul>

<h3>Default Settings</h3>
<ul>
  <li>Enter a default broadcaster name you want to download clips from. When you stop typing, the app checks if the broadcaster exists</li>
  <li>Select a download folder eg. <code>C:\\Username\\TwitchClips</code></li>
  <li>Create a File Name Schema by clicking the available values in your preferred order</li>
  <li>Click "Save Configuration" to save your settings</li>
</ul>

<h2>Instructions: Download clips</h2>
<ol>
  <li>If not already shown, change to the home page by clicking the Twitch icon</li>
  <li>Enter a broadcaster name or use the default name. When you stop typing, the app checks if the broadcaster exists</li>
  <li>Select the date range for searching the clips</li>
  <li>Click "Search Clips" and wait for your results</li>
  <li>All clips are selected for download by default. Click (Ctrl/Shift for multiple) on the clips you want to download. The selected clips are highlighted in green.</li>
  <li>Click "Download Clips" to start the download. The app will show a progress bar and the number of downloaded clips.</li>
  <li>If you want to open the downloaded clips in VLC-Player, click "Download & Open In VLC". Note: This button is only visible if the app found VLC on your system!</li>
</ol>

<h2 id="twitch">Instructions: Create Twitch Client-ID, Client-Secret and OAuth-Token</h2>
<p>This guide describes how to create a Twitch Client-ID, a Client-Secret and an OAuth-Token to use the Twitch API.</p>

<h2>Prerequisites</h2>
<ul>
  <li>A <strong>Twitch account</strong></li>
</ul>

<hr>

<h2>1. Register a new Twitch application</h2>
<ol>
  <li>Log in to your <a href=\"https://dev.twitch.tv/console\">Twitch Developer Dashboard</a>.</li>
  <li>Click on <strong>"Applications"</strong> on the left menu.</li>
  <li>Select <strong>"Register Your Application"</strong>.</li>
  <li>Fill in the required fields:
    <ul>
      <li><strong>Name</strong>: Enter a name for your application (e.g., "tc_dl_twitchname").</li>
      <li><strong>OAuth Redirect URLs</strong>: Enter <code>https://localhost</code></li>
      <li><strong>Category</strong>: Select <code>Other</code>.</li>
      <li><strong>Client Type</strong>: Select <code>Confidential</code></li>
    </ul>
  </li>
  <li>Click on <strong>"Create"</strong>.</li>
</ol>
<p>After creation, your application will be displayed.</p>

<hr>

<h2>2. Retrieve Client-ID and Client-Secret</h2>
<ol>
  <li>Click on the created application on the Twitch Developer Dashboard.</li>
  <li>Select <strong>"Manage"</strong>.</li>
  <li>Scroll down and click on <strong>"New Secret"</strong> to generate a new Client-Secret.</li>
  <li>Copy the displayed <strong>Client-ID</strong> and <strong>Client-Secret</strong> and save them securely. You will need them for future authentications.</li>
</ol>
<p><strong>Note</strong>: Never share the Client-Secret publicly, e.g., in a repository. Use <code>.env</code> files or other secure methods to store sensitive data.</p>

<hr>

<h2>3. Generate an OAuth-Token</h2>
<p>The OAuth token will be generated, updated and saved by the script. No need to worry about.</p>
