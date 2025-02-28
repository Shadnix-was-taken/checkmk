// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef REALTIME_H
#define REALTIME_H

#include <condition_variable>
#include <mutex>
#include <string_view>
#include <thread>

#include "common/cfg_info.h"
#include "encryption.h"

namespace cma::rt {

enum {
    kHeaderSize = 2,
    kTimeStampSize = 10,
    kDataOffset = kHeaderSize + kTimeStampSize
};

constexpr std::string_view kEncryptedHeader{"00"};
constexpr std::string_view kPlainHeader{"99"};

using RtBlock = std::vector<uint8_t>;
using RtTable = std::vector<std::string_view>;

/// crypt is nullptr when encryption is not required
RtBlock PackData(std::string_view output, const encrypt::Commander *crypt);

// uses internal thread
// should be start-stopped
// connectFrom is signal to start actual work thread
class Device {
public:
    Device() = default;
    ~Device() { clear(); }

    Device(const Device &) = delete;
    Device &operator=(const Device &) = delete;

    Device(Device &&) = delete;
    Device &operator=(Device &&) = delete;

    void stop();
    bool start();

    void connectFrom(std::string_view address, int port,
                     const RtTable &sections, std::string_view passphrase,
                     int timeout);

    void connectFrom(std::string_view address, int port,
                     const RtTable &sections, std::string_view passphrase) {
        connectFrom(address, port, sections, passphrase,
                    cfg::kDefaultRealtimeTimeout);
    }

    bool started() const noexcept { return started_; }

    bool working() const noexcept { return working_period_; }

private:
    void mainThread() noexcept;
    std::string generateData() const;

    void clear();
    void resetSections();

    // multi threading area
    mutable std::mutex lock_;
    std::thread thread_;
    std::condition_variable cv_;
    std::atomic<bool> started_{false};
    std::chrono::steady_clock::time_point kick_time_;
    std::string ip_address_;
    std::string passphrase_;
    int port_{0};

    int timeout_{cfg::kDefaultRealtimeTimeout};
    uint64_t kick_count_{0};

    bool working_period_{false};

    bool use_df_{false};
    bool use_mem_{false};
    bool use_winperf_processor_{false};
    bool use_test_{false};

#if defined(ENABLE_WHITE_BOX_TESTING)
    FRIEND_TEST(RealtimeTest, LowLevel);
#endif
};

}  // namespace cma::rt
#endif  // REALTIME_H
