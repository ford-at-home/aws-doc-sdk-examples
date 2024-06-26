// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
/**
 * Before running this C++ code example, set up your development environment, including your credentials.
 *
 * For more information, see the following documentation topic:
 *
 * https://docs.aws.amazon.com/sdk-for-cpp/v1/developer-guide/getting-started.html
 *
 * For information on the structure of the code examples and how to build and run the examples, see
 * https://docs.aws.amazon.com/sdk-for-cpp/v1/developer-guide/getting-started-code-examples.html.
 *
 **/

#include <aws/core/Aws.h>
#include <aws/sns/SNSClient.h>
#include <aws/sns/model/GetSubscriptionAttributesRequest.h>
#include <iostream>
#include "sns_samples.h"


// snippet-start:[sns.cpp.get_subscription_attributes.code]
//! Retrieve the properties of an Amazon Simple Notification Service (Amazon SNS) subscription.
/*!
  \param topicARN: The Amazon Resource Name (ARN) for an SNS subscription.
  \param clientConfiguration: AWS client configuration.
  \return bool: Function succeeded.
 */
bool AwsDoc::SNS::getSubscriptionAttributes(const Aws::String &topicARN,
                                     const Aws::Client::ClientConfiguration &clientConfiguration) {
    Aws::SNS::SNSClient snsClient(clientConfiguration);
    Aws::SNS::Model::GetSubscriptionAttributesRequest request;
    request.SetSubscriptionArn(topicARN);

    const Aws::SNS::Model::GetSubscriptionAttributesOutcome outcome = snsClient.GetSubscriptionAttributes(
            request);

    if (outcome.IsSuccess()) {
        std::cout << "Topic Attributes:" << std::endl;
        for (auto const &attribute: outcome.GetResult().GetAttributes()) {
            std::cout << "  * " << attribute.first << " : " << attribute.second
                      << std::endl;
        }
    }
    else {
        std::cerr << "Error while getting Topic attributes "
                  << outcome.GetError().GetMessage()
                  << std::endl;
    }

    return outcome.IsSuccess();
}
// snippet-end:[sns.cpp.get_subscription_attributes.code]

/*
 *
 *  main function
 *
 *  Usage: 'run_get_subscription_attributes <subscription_arn>'
 *
 *  Prerequisites: An existing SNS subscription and its ARN.
 *
*/

#ifndef TESTING_BUILD

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cout << "Usage: runn_get_subscription_attributes <subscription_arn>" << std::endl;
        return 1;
    }

    Aws::SDKOptions options;

    Aws::InitAPI(options);
    {
        const Aws::String topicARN(argv[1]);

        Aws::Client::ClientConfiguration clientConfig;
        // Optional: Set to the AWS Region (overrides config file).
        // clientConfig.region = "us-east-1";

        AwsDoc::SNS::getSubscriptionAttributes(topicARN, clientConfig);
    }
    Aws::ShutdownAPI(options);
    return 0;
}

#endif // TESTING_BUILD