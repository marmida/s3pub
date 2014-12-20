Feature: Publishing to S3

Scenario: Publishing to an empty bucket
Given that no files exist in the bucket
When I publish new test content to the bucket
Then the test content should be available from the bucket's S3 URL

Scenario: Publishing to an existing bucket
Given that previous test content exists in the bucket
When I publish new test content to the bucket
Then the test content should be available from the bucket's S3 URL
And the previous test content should not be available from the bucket's S3 URL
