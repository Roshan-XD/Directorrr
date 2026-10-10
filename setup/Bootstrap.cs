// Compiled on Windows from this source. Downloads only the reviewed Python ZIP.
using System;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Diagnostics;
using System.ComponentModel;
using System.Windows.Forms;

class Bootstrap : Form {
    const long Bytes = 31153407;
    const string Hash = "bbf675bb5e763c1efbb09a3a461b259d81598a63c30c4b0d7ea11b9f063df159";
    const string Url = "https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.zip";
    readonly string root = Path.GetDirectoryName(typeof(Bootstrap).Assembly.Location);
    readonly Label status = new Label { AutoSize = false, Height = 85, Dock = DockStyle.Top };
    readonly CheckBox accept = new CheckBox { Text = "I reviewed and accept the included Python license terms.", AutoSize = true, Dock = DockStyle.Top };
    readonly Button install = new Button { Text = "Prepare Director setup", Height = 42, Dock = DockStyle.Bottom };
    readonly BackgroundWorker worker = new BackgroundWorker();
    bool running;

    Bootstrap() {
        Text = "Director Setup"; Width = 640; Height = 580;
        StartPosition = FormStartPosition.CenterScreen;
        status.Text = "Director installs privately in this extracted folder. No administrator rights are required.\r\nFirst step: download and verify Python 3.13.16 (31,153,407 bytes). Runtime/model review follows before further downloads.\r\nSystem Python, drivers, Resolve and other installations are left intact.";
        var license = new TextBox { Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Both, Dock = DockStyle.Fill, WordWrap = true };
        var notice = Path.Combine(root, "setup", "notices", "python.txt");
        if (!File.Exists(notice)) throw new InvalidOperationException("Setup license document is missing. Extract the complete release ZIP first.");
        if (Sha(notice) != "62bec384df47b0328307db41455ff6ea2559e5546b394ac69148561b21703120") throw new InvalidOperationException("Python review document checksum changed.");
        license.Text = File.ReadAllText(notice);
        Controls.Add(license); Controls.Add(accept); Controls.Add(status); Controls.Add(install);
        install.Enabled = false;
        accept.CheckedChanged += (s, e) => install.Enabled = accept.Checked && !running;
        worker.DoWork += (s, e) => Prepare();
        worker.RunWorkerCompleted += (s, e) => {
            running = false;
            if (e.Error != null) { MessageBox.Show(e.Error.Message, "Director setup stopped", MessageBoxButtons.OK, MessageBoxIcon.Error); install.Enabled = accept.Checked; }
            else Close();
        };
        install.Click += (s, e) => { running = true; install.Enabled = false; worker.RunWorkerAsync(); };
        FormClosing += (s, e) => { if (running) { e.Cancel = true; MessageBox.Show("Wait for this bounded bootstrap step to finish. The next wizard has cancellation."); } };
    }
    void Status(string text) { BeginInvoke((Action)(() => status.Text = text)); }
    static void Safe(string path) {
        for (var p = new DirectoryInfo(Path.GetFullPath(path)); p != null; p = p.Parent)
            if (p.Exists && (p.Attributes & FileAttributes.ReparsePoint) != 0) throw new InvalidOperationException("Setup paths cannot contain links or junctions.");
        if (File.Exists(path) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) throw new InvalidOperationException("Linked setup file.");
    }
    static string Sha(string path) { using (var f = File.OpenRead(path)) using (var h = SHA256.Create()) return BitConverter.ToString(h.ComputeHash(f)).Replace("-", "").ToLowerInvariant(); }
    void Prepare() {
        Safe(root);
        string native = Path.Combine(root, "runtime", "windows-dev-001");
        string python = Path.Combine(native, "python");
        Safe(native); Safe(python);
        if (Directory.Exists(native)) {
            // Existing installations are inspected by the wizard, never overwritten.
            if (!File.Exists(Path.Combine(native, "owner.json")) || !File.Exists(Path.Combine(python, "pythonw.exe")))
                throw new InvalidOperationException("An incomplete/unknown runtime already occupies this folder. Choose a fresh extracted Director folder; existing data will not be overwritten.");
        } else {
            var drive = new DriveInfo(Path.GetPathRoot(root));
            if (drive.AvailableFreeSpace < 32L * 1024 * 1024 * 1024) throw new InvalidOperationException("Keep at least 32 GiB free for first setup, downloads and verification.");
            string cache = Path.Combine(root, "setup", "state");
            Directory.CreateDirectory(cache); Safe(cache);
            string archive = Path.Combine(cache, "python.zip");
            if (File.Exists(archive)) {
                Safe(archive);
                if (new FileInfo(archive).Length != Bytes || Sha(archive) != Hash) throw new InvalidOperationException("Existing Python download failed integrity. It has been preserved for inspection.");
            } else {
                string partial = archive + ".partial";
                if (File.Exists(partial)) throw new InvalidOperationException("A partial Python download remains. Use a fresh extracted folder; setup does not overwrite unknown files.");
                ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
                var request = (HttpWebRequest)WebRequest.Create(Url);
                request.AllowAutoRedirect = false; request.Timeout = 30000; request.ReadWriteTimeout = 30000;
                using (var response = (HttpWebResponse)request.GetResponse()) {
                    if (response.StatusCode != HttpStatusCode.OK || response.ContentLength != Bytes) throw new InvalidOperationException("Official Python artifact identity/size changed.");
                    using (var source = response.GetResponseStream()) using (var dest = new FileStream(partial, FileMode.CreateNew)) {
                        var buffer = new byte[65536]; int n; long total = 0;
                        while ((n = source.Read(buffer, 0, buffer.Length)) > 0) { total += n; if (total > Bytes) throw new InvalidOperationException("Python transfer exceeded expected size."); dest.Write(buffer, 0, n); Status("Preparing Python: " + total.ToString("N0") + " / " + Bytes.ToString("N0") + " bytes"); }
                    }
                }
                if (new FileInfo(partial).Length != Bytes || Sha(partial) != Hash) throw new InvalidOperationException("Python size/SHA-256 verification failed; no downloaded code was executed.");
                File.Move(partial, archive);
            }
            // Hash before extraction; ordinary bounded files only, never extract-all.
            Status("Python download verified. Extracting into Director-owned storage...");
            using (var zip = ZipFile.OpenRead(archive)) {
                if (zip.Entries.Count > 10000) throw new InvalidOperationException("Python archive entry limit exceeded.");
                long total = 0; var names = new System.Collections.Generic.HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var entry in zip.Entries) {
                    string name = entry.FullName;
                    if (name.Contains("\\") || name.Contains(":") || name.StartsWith("/") || name.Contains("//")) throw new InvalidOperationException("Unsafe Python archive path.");
                    foreach (string part in name.TrimEnd('/').Split('/')) {
                        string stem = part.Split('.')[0].ToUpperInvariant();
                        if (part == "" || part == "." || part == ".." || part.EndsWith(".") || part.EndsWith(" ") || part.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0
                            || stem == "CON" || stem == "PRN" || stem == "AUX" || stem == "NUL" || System.Text.RegularExpressions.Regex.IsMatch(stem, "^(COM|LPT)[1-9]$")) throw new InvalidOperationException("Unsafe Python archive member.");
                    }
                    if (!names.Add(name.TrimEnd('/'))) throw new InvalidOperationException("Duplicate Python member.");
                    int mode = (entry.ExternalAttributes >> 16) & 0xF000;
                    if (mode != 0 && mode != 0x8000 && mode != 0x4000) throw new InvalidOperationException("Special Python archive member.");
                    total += entry.Length;
                    if (entry.Length > 64L * 1024 * 1024 || total > 256L * 1024 * 1024) throw new InvalidOperationException("Python archive extraction limit exceeded.");
                }
                Directory.CreateDirectory(python);
                File.WriteAllText(Path.Combine(native, "owner.json"), "{\"owner\":\"Director Stage 12 private development\",\"production_ready\":false}");
                foreach (var entry in zip.Entries) {
                    string target = Path.GetFullPath(Path.Combine(python, entry.FullName.Replace('/', Path.DirectorySeparatorChar)));
                    if (!target.StartsWith(python + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Python member escapes destination.");
                    Safe(target);
                    if (entry.FullName.EndsWith("/")) { Directory.CreateDirectory(target); continue; }
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    using (var source = entry.Open()) using (var dest = new FileStream(target, FileMode.CreateNew)) {
                        var buffer = new byte[65536]; int n; long written = 0;
                        while ((n = source.Read(buffer, 0, buffer.Length)) > 0) { written += n; if (written > entry.Length) throw new InvalidOperationException("Python member exceeds declared length."); dest.Write(buffer, 0, n); }
                    }
                    if (new FileInfo(target).Length != entry.Length) throw new InvalidOperationException("Python extraction length mismatch.");
                }
            }
            Directory.CreateDirectory(Path.Combine(native, "receipts"));
            File.WriteAllText(Path.Combine(native, "receipts", "bootstrap.json"), "{\"python_sha256\":\"" + Hash + "\",\"private_setup\":true}");
        }
        foreach (var needed in new[] { "pythonw.exe", "python.exe", "Lib/venv/__init__.py", "LICENSE.txt" })
            if (!File.Exists(Path.Combine(python, needed))) throw new InvalidOperationException("Full Python bootstrap is incomplete; embedded distributions are unsupported.");
        string script = Path.Combine(root, "scripts", "teammate_setup.py");
        var start = new ProcessStartInfo(Path.Combine(python, "pythonw.exe"), "-I \"" + script + "\"") { WorkingDirectory = root, UseShellExecute = false };
        Process.Start(start);
    }
    [STAThread] static void Main() {
        Application.EnableVisualStyles();
        try { Application.Run(new Bootstrap()); } catch (Exception e) { MessageBox.Show(e.Message, "Director setup"); }
    }
}
