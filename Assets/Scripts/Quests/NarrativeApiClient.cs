using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

// lets unity turn one gameplay event into json
[Serializable]
// stores scenario start or completion data for backend logs
public class ScenarioRunEvent
{
    // id used to match this event with its narrative request
    public string requestId;

    // selected scenario id and gameplay type
    public string scenarioId;
    public string scenarioType;

    // event name for scenario start or completion
    public string eventType;

    // shows whether the scenario was completed
    public bool completed;

    // gameplay time without the story generation wait
    public float elapsedSeconds;

    // progress values when the event was created
    public int currentProgress;
    public int requiredAmount;

    // shows whether story text came from the backend or local fallback
    public string narrativeSource;

    // shows whether unity accepted the backend story
    public bool backendNarrativeAcceptedByUnity;

    // reason unity rejected the backend story
    public string unityValidationError;

    // reason local fallback text was needed
    public string fallbackReason;
}

// prevents two api clients on the same gameobject
[DisallowMultipleComponent]
// sends story requests and gameplay logs to the backend
public class NarrativeApiClient : MonoBehaviour
{
    // backend url used to request story text
    [SerializeField]
    private string endpoint =
        "http://127.0.0.1:8000/generate-narrative";

    // backend url used to record gameplay events
    [SerializeField]
    private string runEventEndpoint =
        "http://127.0.0.1:8000/record-run-event";

    // maximum wait for each http request in seconds
    [SerializeField, Min(1)]
    private int timeoutSeconds = 60;

    // lets other code read the story request url
    public string Endpoint => endpoint;

    // sends one gameplay event without stopping the quest on failure
    public IEnumerator RecordRunEvent(ScenarioRunEvent runEvent)
    {
        // ignores missing data because logging is optional
        if (runEvent == null)
        {
            yield break;
        }

        // turns the event into json bytes for the request body
        string requestJson = JsonUtility.ToJson(runEvent);
        byte[] requestBody = Encoding.UTF8.GetBytes(requestJson);

        // chooses the event url before creating the request
        string destination = GetRunEventEndpoint();

        // releases network resources when the request ends
        using (UnityWebRequest request =
               new UnityWebRequest(
                   destination,
                   UnityWebRequest.kHttpVerbPOST))
        {
            // adds the json body and stores the backend response
            request.uploadHandler = new UploadHandlerRaw(requestBody);
            request.downloadHandler = new DownloadHandlerBuffer();

            // sets the timeout and json content type
            request.timeout = Mathf.Max(1, timeoutSeconds);
            request.SetRequestHeader("Content-Type", "application/json");

            // waits for the backend without freezing the unity loop
            yield return request.SendWebRequest();

            // reports a log failure without changing the quest
            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning(
                    $"[NarrativeRequest {runEvent.requestId}] Could not " +
                    $"record {runEvent.eventType}: {request.error}",
                    this);
                yield break;
            }

            // reports a successful event request without confirming file storage
            Debug.Log(
                $"[NarrativeRequest {runEvent.requestId}] Recorded " +
                $"{runEvent.eventType} experiment event.",
                this);
        }
    }

    // sends scenario data and returns story text or a failure reason
    // backend fallback text still counts as a successful http response
    public IEnumerator GenerateNarrative(
        NarrativeGenerationRequest requestData,
        Action<GeneratedNarrative> onSuccess,
        Action<string> onFailure)
    {
        // reports missing data before trying to create json
        if (requestData == null)
        {
            onFailure?.Invoke("The narrative request was null.");
            yield break;
        }

        // turns the request into json bytes for the backend
        string requestJson = JsonUtility.ToJson(requestData);
        byte[] requestBody = Encoding.UTF8.GetBytes(requestJson);

        // uses a clear log id when the request id is missing
        string requestId = string.IsNullOrWhiteSpace(requestData.requestId)
            ? "unknown"
            : requestData.requestId;

        // starts timing the backend request
        float startedAt = Time.realtimeSinceStartup;

        // logs the request before waiting for the backend
        Debug.Log(
            $"[NarrativeRequest {requestId}] Sending request to backend.",
            this);

        // releases network resources after success or failure
        using (UnityWebRequest request =
               new UnityWebRequest(endpoint, UnityWebRequest.kHttpVerbPOST))
        {
            // adds the json body and stores the story response
            request.uploadHandler = new UploadHandlerRaw(requestBody);
            request.downloadHandler = new DownloadHandlerBuffer();

            // sets the timeout and json content type
            request.timeout = Mathf.Max(1, timeoutSeconds);
            request.SetRequestHeader("Content-Type", "application/json");

            // waits for the backend without freezing the unity loop
            yield return request.SendWebRequest();

            // sends network or backend errors to the failure callback
            if (request.result != UnityWebRequest.Result.Success)
            {
                // keeps the backend error body when one is available
                string responseBody = request.downloadHandler?.text;
                string message =
                    $"HTTP request failed ({request.responseCode}): " +
                    request.error;

                // adds backend details to the failure message
                if (!string.IsNullOrWhiteSpace(responseBody))
                {
                    message += $" Response: {responseBody}";
                }

                // reports how long the failed request took
                float elapsedSeconds = Time.realtimeSinceStartup - startedAt;
                Debug.LogWarning(
                    $"[NarrativeRequest {requestId}] Failed after " +
                    $"{elapsedSeconds:F2}s. {message}",
                    this);
                onFailure?.Invoke(
                    $"Request {requestId} failed after " +
                    $"{elapsedSeconds:F2}s. {message}");
                yield break;
            }

            // turns successful json into a story object
            GeneratedNarrative narrative;
            try
            {
                narrative = JsonUtility.FromJson<GeneratedNarrative>(
                    request.downloadHandler.text);
            }
            // rejects json that unity cannot read
            catch (ArgumentException error)
            {
                float elapsedSeconds = Time.realtimeSinceStartup - startedAt;
                onFailure?.Invoke(
                    $"Request {requestId} returned invalid narrative JSON " +
                    $"after {elapsedSeconds:F2}s: {error.Message}");
                yield break;
            }

            // rejects an empty story before the success callback
            if (narrative == null)
            {
                float elapsedSeconds = Time.realtimeSinceStartup - startedAt;
                onFailure?.Invoke(
                    $"Request {requestId} returned an empty narrative " +
                    $"after {elapsedSeconds:F2}s.");
                yield break;
            }

            // reports request time and returns the story for validation
            float completedInSeconds = Time.realtimeSinceStartup - startedAt;
            Debug.Log(
                $"[NarrativeRequest {requestId}] Backend response received " +
                $"in {completedInSeconds:F2}s.",
                this);
            onSuccess?.Invoke(narrative);
        }
    }

    // cleans inspector settings when unity validates this component
    private void OnValidate()
    {
        // removes extra spaces from both backend urls
        endpoint = endpoint?.Trim();
        runEventEndpoint = runEventEndpoint?.Trim();

        // keeps the timeout at one second or more
        timeoutSeconds = Mathf.Max(1, timeoutSeconds);
    }

    // chooses the url used for gameplay event logs
    private string GetRunEventEndpoint()
    {
        // uses the inspector url when it is set
        if (!string.IsNullOrWhiteSpace(runEventEndpoint))
        {
            return runEventEndpoint;
        }

        // known story path that can be changed into the event path
        const string generationPath = "/generate-narrative";

        // builds the event url from the story url when possible
        if (!string.IsNullOrWhiteSpace(endpoint) &&
            endpoint.EndsWith(
                generationPath,
                StringComparison.OrdinalIgnoreCase))
        {
            return endpoint.Substring(
                       0,
                       endpoint.Length - generationPath.Length) +
                   "/record-run-event";
        }

        // uses the local event url when no setting works
        return "http://127.0.0.1:8000/record-run-event";
    }
}
