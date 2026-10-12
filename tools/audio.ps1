#Requires -Version 7.0
# Mute control for the default playback device (Game Companion Local).
# get    -> {"endpoint": "...", "muted": bool}
# mute   -> mutes the default device, returns its previous state
# set    -> -Endpoint <id> -Muted true|false restores a recorded state
param(
    [Parameter(Mandatory)][ValidateSet('get', 'mute', 'set')][string]$Action,
    [string]$Endpoint = '',
    [ValidateSet('true', 'false')][string]$Muted = 'false'
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

if (-not ('GclAudio.AudioEndpoint' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace GclAudio
{
    enum EDataFlow { Render = 0, Capture = 1, All = 2 }
    enum ERole { Console = 0, Multimedia = 1, Communications = 2 }

    [ComImport]
    [Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    class MMDeviceEnumeratorComObject { }

    [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(EDataFlow dataFlow, uint stateMask, out IntPtr devices);
        [PreserveSig] int GetDefaultAudioEndpoint(EDataFlow dataFlow, ERole role, out IMMDevice endpoint);
        [PreserveSig] int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice device);
        [PreserveSig] int RegisterEndpointNotificationCallback(IntPtr client);
        [PreserveSig] int UnregisterEndpointNotificationCallback(IntPtr client);
    }

    [Guid("D666063F-1587-4E43-81F1-B948E807363F")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, uint clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object instance);
        [PreserveSig] int OpenPropertyStore(uint access, out IntPtr properties);
        [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
        [PreserveSig] int GetState(out uint state);
    }

    [Guid("5CDF2C82-841E-4546-9722-0CF74078229A")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioEndpointVolume
    {
        [PreserveSig] int RegisterControlChangeNotify(IntPtr notify);
        [PreserveSig] int UnregisterControlChangeNotify(IntPtr notify);
        [PreserveSig] int GetChannelCount(out uint channelCount);
        [PreserveSig] int SetMasterVolumeLevel(float levelDb, ref Guid eventContext);
        [PreserveSig] int SetMasterVolumeLevelScalar(float level, ref Guid eventContext);
        [PreserveSig] int GetMasterVolumeLevel(out float levelDb);
        [PreserveSig] int GetMasterVolumeLevelScalar(out float level);
        [PreserveSig] int SetChannelVolumeLevel(uint channel, float levelDb, ref Guid eventContext);
        [PreserveSig] int SetChannelVolumeLevelScalar(uint channel, float level, ref Guid eventContext);
        [PreserveSig] int GetChannelVolumeLevel(uint channel, out float levelDb);
        [PreserveSig] int GetChannelVolumeLevelScalar(uint channel, out float level);
        [PreserveSig] int SetMute([MarshalAs(UnmanagedType.Bool)] bool muted, ref Guid eventContext);
        [PreserveSig] int GetMute([MarshalAs(UnmanagedType.Bool)] out bool muted);
    }

    public static class AudioEndpoint
    {
        public static string GetDefaultEndpointId()
        {
            IMMDeviceEnumerator enumerator = (IMMDeviceEnumerator)(new MMDeviceEnumeratorComObject());
            IMMDevice device = null;
            try {
                Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(EDataFlow.Render, ERole.Multimedia, out device));
                string id;
                Marshal.ThrowExceptionForHR(device.GetId(out id));
                return id;
            } finally {
                if (device != null) Marshal.ReleaseComObject(device);
                Marshal.ReleaseComObject(enumerator);
            }
        }

        static IAudioEndpointVolume GetEndpointVolume(string endpointId)
        {
            IMMDeviceEnumerator enumerator = (IMMDeviceEnumerator)(new MMDeviceEnumeratorComObject());
            IMMDevice device = null;
            try {
                Marshal.ThrowExceptionForHR(enumerator.GetDevice(endpointId, out device));
                Guid iid = typeof(IAudioEndpointVolume).GUID;
                object instance;
                Marshal.ThrowExceptionForHR(device.Activate(ref iid, 23, IntPtr.Zero, out instance));
                return (IAudioEndpointVolume)instance;
            } finally {
                if (device != null) Marshal.ReleaseComObject(device);
                Marshal.ReleaseComObject(enumerator);
            }
        }

        public static bool GetMute(string endpointId)
        {
            IAudioEndpointVolume endpoint = GetEndpointVolume(endpointId);
            try {
                bool muted;
                Marshal.ThrowExceptionForHR(endpoint.GetMute(out muted));
                return muted;
            } finally { Marshal.ReleaseComObject(endpoint); }
        }

        public static void SetMute(string endpointId, bool muted)
        {
            IAudioEndpointVolume endpoint = GetEndpointVolume(endpointId);
            try {
                Guid context = Guid.Empty;
                Marshal.ThrowExceptionForHR(endpoint.SetMute(muted, ref context));
            } finally { Marshal.ReleaseComObject(endpoint); }
        }
    }
}
'@
}

$id = if ($Endpoint) { $Endpoint } else { [GclAudio.AudioEndpoint]::GetDefaultEndpointId() }
$before = [GclAudio.AudioEndpoint]::GetMute($id)
switch ($Action) {
    'mute' { [GclAudio.AudioEndpoint]::SetMute($id, $true) }
    'set' { [GclAudio.AudioEndpoint]::SetMute($id, $Muted -eq 'true') }
}
$after = [GclAudio.AudioEndpoint]::GetMute($id)
[ordered]@{ endpoint = $id; before = $before; muted = $after } | ConvertTo-Json -Compress
