# File Security Post Scan Actions

Actions to perform after scanning files with Trend Vision One™ File Security

After completing a scan, [File Security displays scan results](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-fs-cli#supported_targets) immediately so you can take action right away to reduce risk and fulfill compliance requirements. Scan results include custom information that is passed to the SDK so you can take further action.

## Procedure

- If File Security indicates a file contains malware, you can take the following actions:
  - Quarantine the file. See a [AWS quarantine example](https://github.com/trendmicro/tm-v1-fs-python-sdk/blob/main/examples/aws_quarantine.py).
  - Send notification messages using:
    - Slack
    - Email
    - Microsoft Teams
- If File Security does not find malware in a file, you can promote the file.
